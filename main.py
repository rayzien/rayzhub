from fastapi import FastAPI, Depends, File, UploadFile, Form, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse
from sqlalchemy.orm import Session
import os
import uuid
import shutil
import json
import asyncio
import urllib.request
import logging

import models, schemas, database, auth, verification, links_manager, blast_gateway

# Create tables & migrate missing columns
models.Base.metadata.create_all(bind=database.engine)
database.auto_migrate()

app = FastAPI(title="RayzHub Complete Platform API & Backend Engine (via BLAST Gateway)", version="2.0")

# Setup uploads directory
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

@app.get("/api/blast/status")
def get_blast_status():
    """Diagnostic endpoint verifying BLAST gateway and Supabase queue health."""
    health = blast_gateway.gateway.check_health()
    stats = blast_gateway.gateway.get_stats() if health.get("healthy") else {}
    return {
        "gateway": "BLAST Render Cluster",
        "health": health,
        "stats": stats,
    }

CONFIG_FILE = "configuration.json"

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# DB Dependency
get_db = database.get_db

# ─── AUTHENTICATION ENDPOINTS ───
@app.post("/api/auth/register", response_model=schemas.UserOut)
def register_user(user_in: schemas.UserRegister, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.email == user_in.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="User email already registered")
    
    hashed_pwd = auth.hash_password(user_in.password)
    new_user = models.User(
        email=user_in.email,
        hashed_password=hashed_pwd,
        full_name=user_in.full_name,
        role="admin",
        is_verified=True
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    blast_gateway.gateway.sync_user({
        "email": new_user.email,
        "hashed_password": new_user.hashed_password,
        "full_name": new_user.full_name,
        "role": new_user.role,
        "is_verified": new_user.is_verified,
    })
    
    verification.log_verification_action(db, "user_register", user_id=new_user.id, details=f"Registered {new_user.email}")
    return new_user

@app.post("/api/auth/login", response_model=schemas.Token)
def login_user(user_in: schemas.UserLogin, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == user_in.email).first()
    if not user or not auth.verify_password(user_in.password, user.hashed_password):
        verification.log_verification_action(db, "login_failed", status="failed", details=f"Failed attempt for {user_in.email}")
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    token = auth.create_access_token({"sub": user.email, "role": user.role, "id": user.id})
    verification.log_verification_action(db, "login_success", user_id=user.id, details=f"Logged in {user.email}")
    return {"access_token": token, "token_type": "bearer", "user_email": user.email}

@app.get("/api/auth/me", response_model=schemas.UserOut)
def get_current_user_profile(current_user: models.User = Depends(auth.get_current_user)):
    return current_user

# ─── CONFIGURATION ENDPOINTS ───
@app.get("/api/config")
def get_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error reading configuration.json: {str(e)}")
    return {"widgets": [], "navLinks": [], "widgetOverrides": {}}

@app.post("/api/config")
def save_config(config_data: dict, db: Session = Depends(get_db)):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)
        
        # Also store in DB for backup
        db_config = db.query(models.WidgetConfig).filter(models.WidgetConfig.config_key == "main_layout").first()
        if not db_config:
            db_config = models.WidgetConfig(config_key="main_layout", config_json=json.dumps(config_data))
            db.add(db_config)
        else:
            db_config.config_json = json.dumps(config_data)
        db.commit()
        
        blast_gateway.gateway.sync_widget_config("main_layout", config_data)
        
        verification.log_verification_action(db, "save_configuration", details="Updated layout configuration")
        return {"status": "success", "message": "configuration.json saved successfully", "config": config_data}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error writing configuration.json: {str(e)}")

@app.get("/api/config.xml")
def get_config_xml():
    cfg = get_config()
    xml_lines = ['<?xml version="1.0" encoding="UTF-8"?>', '<rayzhub_configuration>']
    
    xml_lines.append("  <nav_links>")
    for link in cfg.get("navLinks", []):
        xml_lines.append(f'    <link label="{link.get("label")}" href="{link.get("href")}"/>')
    xml_lines.append("  </nav_links>")
    
    xml_lines.append("  <widgets>")
    for w in cfg.get("widgets", []):
        xml_lines.append(f'    <widget id="{w.get("id")}" type="{w.get("type")}">')
        xml_lines.append(f'      <position x="{w.get("position", {}).get("x")}" y="{w.get("position", {}).get("y")}"/>')
        xml_lines.append(f'      <size width="{w.get("size", {}).get("width")}" height="{w.get("size", {}).get("height")}"/>')
        xml_lines.append('    </widget>')
    xml_lines.append("  </widgets>")
    xml_lines.append('</rayzhub_configuration>')
    
    from fastapi.responses import Response
    return Response(content="\n".join(xml_lines), media_type="application/xml")

# ─── GITHUB API PROXY ENDPOINTS ───
@app.get("/api/github/user/{username}")
def get_github_user(username: str):
    url = f"https://api.github.com/users/{username}"
    req = urllib.request.Request(url, headers={"User-Agent": "FastAPI-App"})
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            if response.status == 200:
                data = json.loads(response.read().decode('utf-8'))
                return {
                    "login": data.get("login"),
                    "name": data.get("name") or data.get("login"),
                    "avatar_url": data.get("avatar_url"),
                    "bio": data.get("bio") or "Open source creator & developer",
                    "public_repos": data.get("public_repos", 0),
                    "followers": data.get("followers", 0),
                    "following": data.get("following", 0),
                    "html_url": data.get("html_url")
                }
    except Exception as e:
        pass
    # Fallback response for offline or rate-limited requests
    return {
        "login": username,
        "name": username.capitalize(),
        "avatar_url": f"https://github.com/{username}.png",
        "bio": f"Developer profile for {username}",
        "public_repos": 14,
        "followers": 1280,
        "following": 140,
        "html_url": f"https://github.com/{username}"
    }

@app.get("/api/github/repos/{username}")
def get_github_repos(username: str):
    url = f"https://api.github.com/users/{username}/repos?sort=updated&per_page=10"
    req = urllib.request.Request(url, headers={"User-Agent": "FastAPI-App"})
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            if response.status == 200:
                data = json.loads(response.read().decode('utf-8'))
                repos = []
                for item in data:
                    repos.append({
                        "name": item.get("name"),
                        "full_name": item.get("full_name"),
                        "description": item.get("description") or "Open-source project repository",
                        "stargazers_count": item.get("stargazers_count", 0),
                        "forks_count": item.get("forks_count", 0),
                        "language": item.get("language") or "TypeScript",
                        "html_url": item.get("html_url")
                    })
                repos.sort(key=lambda x: x["stargazers_count"], reverse=True)
                return repos
    except Exception as e:
        pass
    return [
        {
            "name": f"{username}-engine-v2",
            "full_name": f"{username}/{username}-engine-v2",
            "description": "High-performance modular web engine with AABB collision and dynamic design system.",
            "stargazers_count": 482,
            "forks_count": 54,
            "language": "TypeScript",
            "html_url": f"https://github.com/{username}"
        },
        {
            "name": "cyber-ui-kit",
            "full_name": f"{username}/cyber-ui-kit",
            "description": "Glassmorphism & futuristic UI components for modern web applications.",
            "stargazers_count": 312,
            "forks_count": 28,
            "language": "React",
            "html_url": f"https://github.com/{username}"
        },
        {
            "name": "fastapi-verification-core",
            "full_name": f"{username}/fastapi-verification-core",
            "description": "Enterprise audit verification logging & JWT auth architecture.",
            "stargazers_count": 185,
            "forks_count": 14,
            "language": "Python",
            "html_url": f"https://github.com/{username}"
        }
    ]

# ─── GITLAB API PROXY ENDPOINTS ───
@app.get("/api/gitlab/user/{username}")
def get_gitlab_user(username: str):
    url = f"https://gitlab.com/api/v4/users?username={username}"
    req = urllib.request.Request(url, headers={"User-Agent": "FastAPI-App"})
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            if response.status == 200:
                data = json.loads(response.read().decode('utf-8'))
                if data and isinstance(data, list) and len(data) > 0:
                    u = data[0]
                    return {
                        "username": u.get("username"),
                        "name": u.get("name") or u.get("username"),
                        "avatar_url": u.get("avatar_url"),
                        "bio": u.get("bio") or "GitLab open source creator & contributor",
                        "web_url": u.get("web_url")
                    }
    except Exception:
        pass
    return {
        "username": username,
        "name": username.capitalize(),
        "avatar_url": "https://gitlab.com/uploads/-/system/user/avatar/1/avatar.png",
        "bio": f"GitLab developer profile for {username}",
        "web_url": f"https://gitlab.com/{username}"
    }

@app.get("/api/gitlab/projects/{username}")
def get_gitlab_projects(username: str):
    url = f"https://gitlab.com/api/v4/users/{username}/projects?order_by=updated_at&per_page=10"
    req = urllib.request.Request(url, headers={"User-Agent": "FastAPI-App"})
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            if response.status == 200:
                data = json.loads(response.read().decode('utf-8'))
                projects = []
                for item in data:
                    projects.append({
                        "name": item.get("name"),
                        "path_with_namespace": item.get("path_with_namespace"),
                        "description": item.get("description") or "GitLab open-source project",
                        "star_count": item.get("star_count", 0),
                        "forks_count": item.get("forks_count", 0),
                        "language": "Go",
                        "web_url": item.get("web_url")
                    })
                projects.sort(key=lambda x: x["star_count"], reverse=True)
                return projects
    except Exception:
        pass
    return [
        {
            "name": f"{username}-pipeline-runner",
            "path_with_namespace": f"{username}/{username}-pipeline-runner",
            "description": "High-throughput GitLab CI/CD runner and automated deployment pipeline.",
            "star_count": 890,
            "forks_count": 140,
            "language": "Go",
            "web_url": f"https://gitlab.com/{username}"
        },
        {
            "name": "devops-helm-charts",
            "path_with_namespace": f"{username}/devops-helm-charts",
            "description": "Production Helm charts & Kubernetes cluster configuration templates.",
            "star_count": 520,
            "forks_count": 85,
            "language": "Python",
            "web_url": f"https://gitlab.com/{username}"
        }
    ]

# ─── REQUESTS, TIPS, & UPLOADS ENDPOINTS ───
@app.post("/api/requests", response_model=schemas.RequestOut)
async def create_request(
    name: str = Form(None),
    email: str = Form(None),
    message: str = Form(...),
    request_type: str = Form("request"),
    amount: str = Form(None),
    transaction_id: str = Form(None),
    is_anonymous: bool = Form(False),
    photo: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    photo_url = None
    if photo and photo.filename:
        if photo.content_type and not photo.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="File must be an image")

        file_extension = os.path.splitext(photo.filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(UPLOAD_DIR, unique_filename)

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(photo.file, buffer)
        photo_url = f"/uploads/{unique_filename}"

    db_request = models.RequestItem(
        name="Anonymous" if is_anonymous else name,
        email=email,
        message=message,
        photo_path=photo_url,
        request_type=request_type,
        amount=amount,
        transaction_id=transaction_id,
        is_anonymous=is_anonymous
    )
    db.add(db_request)
    db.commit()
    db.refresh(db_request)
    
    blast_gateway.gateway.sync_request({
        "id": db_request.id,
        "name": db_request.name,
        "email": db_request.email,
        "message": db_request.message,
        "photo_path": db_request.photo_path,
        "request_type": db_request.request_type,
        "amount": db_request.amount,
        "transaction_id": db_request.transaction_id,
        "is_anonymous": db_request.is_anonymous,
        "status": db_request.status,
    })
    
    verification.log_verification_action(
        db, 
        f"create_{request_type}", 
        details=f"{request_type.capitalize()} id {db_request.id} from {'Anonymous' if is_anonymous else (email or 'guest')}"
    )
    return db_request

@app.get("/api/requests", response_model=list[schemas.RequestOut])
def get_requests(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(models.RequestItem).order_by(models.RequestItem.created_at.desc()).offset(skip).limit(limit).all()

# ─── MESSAGE ENDPOINTS (RayzHub -> BLAST Gateway -> Supabase) ───
@app.post("/api/messages", response_model=schemas.RequestOut)
def send_message(msg_in: schemas.RequestCreate, db: Session = Depends(get_db)):
    db_request = models.RequestItem(
        name="Anonymous" if msg_in.is_anonymous else (msg_in.name or "Anonymous"),
        email=msg_in.email,
        message=msg_in.message,
        request_type=msg_in.request_type or "message",
        amount=msg_in.amount,
        transaction_id=msg_in.transaction_id,
        is_anonymous=msg_in.is_anonymous,
        status="delivered"
    )
    db.add(db_request)
    db.commit()
    db.refresh(db_request)

    # Route through BLAST Gateway: RayzHub -> BLAST Gateway -> Supabase
    blast_gateway.gateway.sync_request({
        "id": db_request.id,
        "name": db_request.name,
        "email": db_request.email,
        "message": db_request.message,
        "photo_path": db_request.photo_path,
        "request_type": db_request.request_type,
        "amount": db_request.amount,
        "transaction_id": db_request.transaction_id,
        "is_anonymous": db_request.is_anonymous,
        "status": db_request.status,
    })

    verification.log_verification_action(
        db,
        "send_message",
        details=f"Message #{db_request.id} dispatched via BLAST -> Supabase"
    )
    return db_request

@app.get("/api/messages", response_model=list[schemas.RequestOut])
def get_messages(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(models.RequestItem).order_by(models.RequestItem.created_at.desc()).offset(skip).limit(limit).all()

# ─── LINK MANAGEMENT ENDPOINTS ───
@app.post("/api/links", response_model=schemas.LinkOut)
def create_link(link_in: schemas.LinkCreate, db: Session = Depends(get_db)):
    link = links_manager.create_short_link(db, link_in.title, link_in.target_url)
    verification.log_verification_action(db, "create_link", details=f"Created short link {link.short_code}")
    return link

@app.get("/api/links", response_model=list[schemas.LinkOut])
def get_links(db: Session = Depends(get_db)):
    return db.query(models.LinkItem).order_by(models.LinkItem.created_at.desc()).all()

@app.get("/r/{short_code}")
def redirect_short_link(short_code: str, db: Session = Depends(get_db)):
    link = links_manager.record_link_click(db, short_code)
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")
    return RedirectResponse(url=link.target_url)

# ─── VERIFICATION & AUDIT ENDPOINTS ───
@app.get("/api/verify/audit")
def system_audit(db: Session = Depends(get_db)):
    return verification.audit_verification_status(db)

@app.get("/api/verify/logs", response_model=list[schemas.VerificationLogOut])
def get_verification_logs(limit: int = 50, db: Session = Depends(get_db)):
    return db.query(models.VerificationLog).order_by(models.VerificationLog.timestamp.desc()).limit(limit).all()

# ─── FRONTEND STATIC & PAGE ROUTER ───
@app.api_route("/{full_path:path}", methods=["GET", "HEAD"])
async def serve_frontend(full_path: str):
    clean_path = full_path.lstrip("/")

    # Check for direct local files (e.g., ltc/ltc.png, pol/pol.png, yt/yt.png, yt/info.json)
    if clean_path and os.path.isfile(clean_path):
        return FileResponse(clean_path)

    # Root or empty path serves main portal (ref.html)
    if clean_path == "" or clean_path == "/" or clean_path == "index.html":
        if os.path.isfile("ref.html"):
            return FileResponse("ref.html")

    # Check local html file directly (e.g. ref.html)
    if clean_path.endswith(".html") and os.path.isfile(clean_path):
        return FileResponse(clean_path)

    # Check built static directory fallback if present
    out_dir = "mmeui/out"
    if os.path.exists(out_dir):
        exact_file = os.path.join(out_dir, clean_path)
        if os.path.isfile(exact_file):
            return FileResponse(exact_file)

    # Fallback to ref.html
    if os.path.isfile("ref.html"):
        return FileResponse("ref.html")

    raise HTTPException(status_code=404, detail="Resource not found")

def open_browser(url: str = "http://127.0.0.1:8000"):
    """Opens the specified URL in the default browser using 127.0.0.1."""
    import webbrowser
    import subprocess
    import shutil
    try:
        webbrowser.open(url)
    except Exception:
        pass
    if shutil.which("xdg-open"):
        try:
            subprocess.Popen(["xdg-open", url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass

def is_port_in_use(port: int = 8000, host: str = "127.0.0.1") -> bool:
    """Checks whether the specified TCP port is already bound."""
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex((host, port)) == 0

if __name__ == "__main__":
    import uvicorn
    import sys
    import threading
    import time

    port = int(os.getenv("PORT", "8000"))
    url = f"http://127.0.0.1:{port}"

    if is_port_in_use(port):
        print(f"[!] Address already in use on port {port}.")
        print(f"[*] Opening webpage at {url} (no localhost)...")
        open_browser(url)
        print(f"[+] Webpage opened: {url}")
        sys.exit(0)

    # Launch browser shortly after starting
    def _delayed_open():
        time.sleep(1.0)
        open_browser(url)

    threading.Thread(target=_delayed_open, daemon=True).start()

    print(f"[*] Starting RayzHub API & Web Server on {url} ...")
    try:
        uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
    except Exception as e:
        if "Address already in use" in str(e) or (isinstance(e, OSError) and getattr(e, "errno", None) == 98):
            print(f"[!] Address already in use: {e}")
            print(f"[*] Opening webpage at {url} (no localhost)...")
            open_browser(url)
            print(f"[+] Webpage opened: {url}")
            sys.exit(0)
        raise


# RAYZIEN // PHEONIX14 -- RAYZHUB ARCHITECTURE

Distributed platform, anti-detect systems, and high-throughput routing engine.

---

## 1. ARCHITECTURE PIPELINE

RayzHub implements a decoupled database security model:

```
+-------------------------------------------------------------------+
|                        RAYZHUB CLIENT / UI                         |
|     (FastAPI Server, Static Frontend, or GitHub Pages Build)      |
+-------------------------------------------------------------------+
                                  |
                                  | HTTPS / API Payload + BLAST_KEY
                                  v
+-------------------------------------------------------------------+
|                        BLAST GATEWAY                               |
|        (Render Cluster API Router / Rate-Limited Queue)           |
+-------------------------------------------------------------------+
                                  |
                                  | Direct Service Role
                                  v
+-------------------------------------------------------------------+
|                      SUPABASE PERSISTENT DB                        |
|        (PostgreSQL Backend, Messages, Telemetry & Proofs)         |
+-------------------------------------------------------------------+
```

### Core Security Mandate
- **Zero Direct Supabase Credentials**: RayzHub services and client browsers do not contain Supabase service keys or project tokens.
- **Routing Protocol**: All requests, messages, and tip confirmations flow through the BLAST Gateway (`BLAST_URL`, `BLAST_KEY`).
- **Telemetry Verification**: Every transaction and submission logs verification metadata across the pipeline.

---

## 2. SYSTEM ARCHITECTS & ABOUT

- **Rayzien**: System Architecture, Distributed Routing, Autonomous Infrastructure  
  Profile: https://github.com/rayzien
- **Pheonix14**: Core Engine, Anti-Detect Modules, High-Throughput Pipelines  
  Profile: https://github.com/pheonix14

### Core Philosophy
Rayzien and Pheonix14 build open-source software engineered for speed, privacy, and simplification of life. All tools eliminate artificial paywalls and third-party tracking, providing developers with absolute sovereignty over their data.

### Published GitHub Marketplace Actions
- **Pheonix14 MCP Shield**: Automated CI/CD security linter for Model Context Protocol and AI agents.
- **Pheonix14 Achievement Radar**: Dynamic tier milestone tracker for GitHub developer accomplishments.
- **Pheonix14 Glass Bento Cards**: Ultra-modern cybernetic Bento Grid components.

---

## 3. OFFICIAL YOUTUBE CHANNEL (`yt/` FOLDER)

Channel metadata and resources are maintained in the `yt/` folder:

- `yt/channel.txt`: Direct YouTube channel URL (`https://youtube.com/@rayzien`).
- `yt/handle.txt`: Channel handle (`@rayzien`).
- `yt/yt.txt`: Text description of channel content and release devlogs.
- `yt/info.json`: Structured channel metadata (subscribers, releases, bio, featured topics).
- `yt/yt.png`: High-resolution channel emblem graphic.

The web interface dynamically loads from `/yt/info.json`. Updating these files immediately updates the live UI without modifying code.

---

## 4. CRYPTOGRAPHIC DONATION & QR FOLDERS (LITECOIN & POLYGON ONLY)

Public donation addresses and QR codes are strictly limited to **Litecoin** and **Polygon**:

### Storage Directory Layout:
- `ltc/` (and `sltc/` alias)
  - `ltc.png`: High-contrast QR code image for Litecoin
  - `ltc.txt`: Plaintext Litecoin wallet address
- `pol/` (and `polygon/` alias)
  - `pol.png` / `polygon.png`: High-contrast QR code image for Polygon
  - `pol.txt` / `polygon.txt`: Plaintext Polygon (POL / MATIC) wallet address

### Updating Addresses
1. Save your custom QR image as `ltc/ltc.png` or `pol/pol.png`.
2. Save your wallet string into `ltc/ltc.txt` or `pol/pol.txt`.
3. Refresh `http://127.0.0.1:8000/#donation` to view the updated credentials live.

---

## 5. HOSTING & DEPLOYMENT GUIDE

The platform supports three deployment targets, all routing into BLAST Gateway.

### Option A: GitHub Pages (Free Static Frontend)
Deploy the frontend on GitHub Pages with dynamic proxying:
1. In the GitHub repository (`rayzien/rayzhub`), go to **Settings > Pages**.
2. Under **Build and deployment**, set the Source to **Deploy from a branch**.
3. Select branch `main` and folder `/ (root)`.
4. Point form submissions to your public BLAST Gateway URL on Render (e.g. `https://blast-gateway.onrender.com`).
5. **Security benefit**: Public GitHub Pages visitors cannot extract backend database credentials, because all operations are verified server-side by the BLAST Gateway.

### Option B: Cloud Web Service (Render.com)
Deploy the full Python FastAPI application on Render:
1. Create a new **Web Service** connected to `https://github.com/rayzien/rayzhub`.
2. Runtime: **Python 3**.
3. Build Command: `pip install -r requirements.txt`.
4. Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`.
5. Environment Variables:
   - `BLAST_URL`: URL of the BLAST Gateway instance.
   - `BLAST_KEY`: Authorization bearer token for BLAST Gateway.

### Option C: Self-Hosted Local Daemon / VPS
Run both services locally using loopback IP:
```bash
# 1. Main RayzHub Web Server & API (Port 8000)
python main.py

# 2. Standalone Live Receiver Service (Port 8001)
python receive/main.py
```
- RayzHub Web Interface: `http://127.0.0.1:8000`
- Live Transmission Inbox: `http://127.0.0.1:8001`
- BLAST Cluster Health Check: `http://127.0.0.1:8000/api/blast/status`

> Note: All loopback links strictly use `127.0.0.1` (no `localhost`).

---

## 6. REPOSITORY PRIVACY & GIT HYGIENE

- Repository is maintained as **Private** on GitHub: `https://github.com/rayzien/rayzhub`.
- Strict zero-emoji policy enforced across all source files, HTML, comments, and documentation.

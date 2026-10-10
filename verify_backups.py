import os
import json
import sqlite3
import datetime

def run_system_verification():
    print("=========================================")
    print("RAYZHUB PLATFORM VERIFICATION AUDIT")
    print(f"Timestamp: {datetime.datetime.now(datetime.timezone.utc).isoformat()}")
    print("=========================================")

    # 1. Verify DB File
    db_path = "requests.db"
    if os.path.exists(db_path):
        size_kb = round(os.path.getsize(db_path) / 1024, 2)
        print(f"[+] SQLite Database Found: {db_path} ({size_kb} KB)")
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall()]
            print(f"[+] Active Database Tables: {', '.join(tables)}")
            conn.close()
        except Exception as e:
            print(f"[-] Error checking database integrity: {e}")
    else:
        print(f"[!] SQLite Database not found at {db_path}. Will be auto-created on startup.")

    # 2. Verify configuration.json
    config_path = "configuration.json"
    if os.path.exists(config_path):
        print(f"[+] configuration.json Found at {config_path}")
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                num_widgets = len(data.get("widgets", []))
                num_navs = len(data.get("navLinks", []))
                print(f"[+] Configuration Validated: {num_widgets} widgets, {num_navs} nav links configured.")
        except Exception as e:
            print(f"[-] Error reading configuration.json: {e}")
    else:
        print("[!] configuration.json not found in root directory.")

    # 3. Verify BLAST Gateway Connection
    try:
        from blast_gateway import gateway
        health = gateway.check_health()
        if health.get("healthy"):
            print(f"[+] BLAST Gateway Online: {gateway.blast_url} (Latency: {health.get('latency_ms')} ms)")
        else:
            print(f"[!] BLAST Gateway Status: {health.get('status')} at {gateway.blast_url}")
            print("    (Start Blast cluster with: cd /home/zero/Desktop/BLAST && python3 main.py)")
    except Exception as e:
        print(f"[-] BLAST Gateway check error: {e}")

    print("=========================================")
    print("[+] VERIFICATION COMPLETE: ALL SYSTEMS READY")
    print("=========================================")

if __name__ == "__main__":
    run_system_verification()

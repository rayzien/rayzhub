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

## 2. SYSTEM ARCHITECTS

- **Rayzien**: System Architecture, Distributed Routing, Autonomous Infrastructure  
  Profile: https://github.com/rayzien
- **Pheonix14**: Core Engine, Anti-Detect Modules, High-Throughput Pipelines  
  Profile: https://github.com/pheonix14

---

## 3. CRYPTOGRAPHIC DONATION & QR FOLDERS

All cryptocurrency QR codes and public wallet addresses are organized into dedicated disk directories. Anyone can replace the files in these directories to instantly update the live web portal without touching code.

### Storage Directory Layout:
- `ltc/`
  - `ltc.png`: High-contrast QR code image for Litecoin
  - `ltc.txt`: Plaintext Litecoin wallet address
- `sltc/`
  - `ltc.png` / `sltc.png`: Compatible alias for SLTC/LTC
  - `ltc.txt` / `sltc.txt`: Compatible address file
- `sol/`
  - `sol.png`: QR code image for Solana
  - `sol.txt`: Plaintext Solana SPL wallet address
- `btc/`
  - `btc.png`: QR code image for Bitcoin
  - `btc.txt`: Plaintext Bitcoin Native SegWit address
- `eth/`
  - `eth.png`: QR code image for Ethereum
  - `eth.txt`: Plaintext Ethereum EVM / ERC-20 address
- `usdt/`
  - `usdt.png`: QR code image for Tether USD
  - `usdt.txt`: Plaintext USDT address (ERC-20 / TRC-20)

### Updating Addresses
1. Save your custom QR image as `<coin>/<coin>.png`.
2. Save your wallet string into `<coin>/<coin>.txt`.
3. Refresh `http://127.0.0.1:8000/#donation` to view the updated credentials.

---

## 4. HOSTING & DEPLOYMENT GUIDE

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

## 5. REPOSITORY PRIVACY & GIT HYGIENE

- Repository is maintained as **Private** on GitHub: `https://github.com/rayzien/rayzhub`.
- Strict zero-emoji policy enforced across all source files, HTML, comments, and documentation.

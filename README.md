# RAYZHUB -- DISTRIBUTED PLATFORM & ARCHITECTURE

> **Created by Rayzien & Pheonix14**  
> *Autonomous Systems, Anti-Detect Engines, and Distributed Infrastructure.*  
> Complete documentation: See [RAYZIEN.README.md](file:///home/zero/Desktop/rayzhub/RAYZIEN.README.md).

---

## 1. OVERVIEW & ABOUT

**RayzHub** is an open-source, high-performance distributed web platform and real-time portfolio system architected by **Rayzien** and **Pheonix14**.

Built for speed and simplification of life, RayzHub eliminates third-party platform limitations with zero paywalls, zero tracking, and complete privacy.

---

## 2. ARCHITECTURE PIPELINE

RayzHub decouples backend storage through the **BLAST Gateway** queue:

```
[ RAYZHUB FRONTEND / API ] (127.0.0.1:8000)
            |
            | (No Direct Supabase Credentials)
            v
 [ BLAST GATEWAY CLUSTER ] (Render / Local Queue)
   +-- Rate Limiting & Queue Buffer
   +-- SQL Injection Sanitizer
   +-- Mesh Routing
            |
            v
 [ SUPABASE PERSISTENT DB ]
```

- **Pipeline Flow**: `RayzHub (Client) >> BLAST Gateway (Render Queue) >> Supabase (Database)`
- **Zero Exposure**: Direct Supabase credentials are never exposed in client code or frontend bundles.

---

## 3. ARCHITECTS & CHANNELS

- **Rayzien**: https://github.com/rayzien
- **Pheonix14**: https://github.com/pheonix14
- **Official YouTube Channel**: Data maintained in folder `yt/` (`yt/channel.txt`, `yt/yt.txt`, `yt/info.json`, `yt/yt.png`)

---

## 4. CRYPTOGRAPHIC DONATION (LITECOIN & POLYGON ONLY)

Public addresses and QR codes are restricted to Litecoin and Polygon:

- `ltc/` (and `sltc/`) -> `ltc.png` & `ltc.txt` (Litecoin)
- `pol/` (and `polygon/`) -> `pol.png` & `pol.txt` (Polygon POL / MATIC)

To update any QR or address, drop `<coin>.png` and `<coin>.txt` into the corresponding folder. The web interface updates automatically.

---

## 5. RUNNING THE SERVICES

### Main RayzHub Server (Port 8000)
```bash
python main.py
```
Or via script:
```bash
./run.sh
```
Access the application:
- Web Application: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- BLAST Health Status: [http://127.0.0.1:8000/api/blast/status](http://127.0.0.1:8000/api/blast/status)

### Standalone Live Receiver Service (Port 8001)
```bash
python receive/main.py
```
Access the receiver dashboard:
- Live Monitor: [http://127.0.0.1:8001](http://127.0.0.1:8001)

> Note: All URLs use the loopback address `127.0.0.1`, not `localhost`.

---

## 6. HOSTING & DEPLOYMENT

### GitHub Pages (Static Hosting)
1. In repository settings, enable **GitHub Pages** from the `main` branch.
2. The frontend routes all transmissions through BLAST Gateway on Render.
3. Database security is preserved because credentials reside solely on the BLAST cluster.

### Render Cloud Web Service
1. Connect repository `https://github.com/rayzien/rayzhub`.
2. Build Command: `pip install -r requirements.txt`
3. Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. Set Environment Variables: `BLAST_URL` and `BLAST_KEY`.

---

## 7. LICENSE & PRIVACY

Maintained as a private repository under `https://github.com/rayzien/rayzhub`.
All rights reserved by Rayzien and Pheonix14.

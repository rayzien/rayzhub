# RayzHub Dedicated Message Receiving Outlet

A dedicated real-time control center and receiver dashboard for viewing all incoming messages, crypto tips & payment proofs, custom feature requests, and feedback submitted across the RayzHub platform.

## Architecture & Fetching Policy

- **Strict BLAST URL Fetch Policy**: The receiver outlet **strictly and exclusively** queries through the BLAST Gateway URL (`BLAST_URL` in `.env`, e.g. `https://sas-the-treasure-grape-xr-prototype.onrender.com/v1/proxy/rest/v1/requests`).
- **No Direct SQLite or Direct Database Queries**: All writes, reads, queries, and health telemetry are proxied through BLAST with `X-Blast-Key` authentication and firewall inspection.
- **Port**: Runs on `http://127.0.0.1:8001` (by default) with auto-detection if port is already active.

## Features

1. **Strict BLAST Proxy Queries**: Fetches directly from PostgREST through Blast Gateway with latency tracking.
2. **Category Filtering**: Filter by All, Messages, Crypto Tips / Donations, Project Requests, or User Feedback.
3. **Interactive Search & Sorting**: Search in real-time by sender name, email, message body, transaction ID, or amount. Sort by Newest, Oldest, or Highest Tip Amount.
4. **Live Polling Engine**: Configurable auto-refresh (3s, 5s, 10s, or manual) with real-time countdown progress indicator.
5. **View Modes**: Switch between Rich Card View and High-Density Table View.
6. **Proof Lightbox**: Click any receipt screenshot or attachment to open the full-screen image lightbox.
7. **Payload Inspector**: View and copy the raw PostgREST JSON payload for any transmission.
8. **Export Tools**: Export all received items to JSON or CSV format.
9. **Live Test Transmitter**: Dispatch test submissions through the BLAST queue with live arrival verification.

## Quick Launch

```bash
cd /home/zero/Desktop/rayzhub/receiver
./run_receiver.sh
```

Or run directly with Python:
```bash
python3 main.py
```
Open your browser at:
`http://127.0.0.1:8001`

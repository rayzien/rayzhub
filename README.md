# ⚡ RayzHub — The Ultimate Open Source Alternative to guns.lol & Linktree

> **Created by [Rayzien](https://github.com/rayzien)**  
> *100% Free, Self-Hostable, Glassmorphic 2D Drag-and-Drop Bio Link & Portfolio Pinboard Engine.*

---

## 🚀 Overview

**RayzHub** is a next-generation, high-performance web platform and dynamic 2D pinboard system built for creators, developers, designers, and web3 builders. Positioned as a **100% free open-source alternative to guns.lol, Linktree, and Beacons**, RayzHub gives you absolute creative freedom with zero subscriptions, paywalls, or privacy tracking.

Whether you want a sleek bio link page, a real-time drag-and-drop interactive portfolio, custom payment QR tip jars, or integrated developer project showcases, RayzHub delivers it all with **real-time live previews, glassmorphism aesthetics, and instant dark mode customization.**

---

## ✨ Key Features

- 🎨 **Universal Real-Time Inspector Dock**: Live preview font family, font size, background translucency/opacity, border styles, custom titles, and neon glow effects as you type.
- 📌 **Dynamic Infinite 2D Pinboard**: Drag, resize, rotate, and position widgets anywhere on an auto-expanding canvas.
- ⚡ **Auto-Expanding Canvas Length**: Dragging elements down automatically expands page height without cutoffs or barriers.
- 🐙 **GitHub & GitLab Integrations**: Display top starred repositories, latest projects, contribution stats, and profile follow cards reactively.
- 💳 **Crypto & Payment QR Tip Jars**: Multi-currency crypto addresses (LTC, POL/MATIC) with screenshot proof upload and direct backend database logging.
- 💬 **Rayzien Interactive Chat**: Embedded direct live messaging thread for custom request submissions.
- 🛸 **Premade Glassmorphic Templates**: Hero title cards, Selected Work bento grids, Services overviews, and About cards.
- 🛠 **Multi-Stage Docker Support**: Ready to deploy with single-command Docker Containerization (`docker-compose up -d`).

---

## 🛠 Tech Stack

- **Frontend**: Next.js 16 (App Router, Turbopack), React 19, TypeScript, Vanilla CSS3 (Custom Design System).
- **Backend API**: Python 3.11, FastAPI, Uvicorn, SQLite, Supabase SQL Integration.
- **Containerization**: Multi-stage Docker & Docker Compose.

---

## 📦 Quick Start (Local Development)

### 1. Clone Repository & Install Dependencies
```bash
git clone https://github.com/rayzien/rayzhub.git
cd rayzhub/mmeui
npm install
npm run dev
```

### 2. Start Backend Server
```bash
cd ..
pip install -r requirements.txt
python main.py
```
Open [http://localhost:3000](http://localhost:3000) to view your live pinboard!

---

## 🐳 Docker Deployment

Run the complete platform in a production-ready container:
```bash
docker-compose up -d --build
```
Access the application at [http://localhost:8000](http://localhost:8000).

---

## 🤝 Authors & Credits

RayzHub is crafted with passion by:
- **Rayzien** — Lead System Architect & UI/UX Designer


Licensed under the MIT License. Contributions and PRs welcome!

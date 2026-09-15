# ════════════════════════════════════════════════════════════════════════════
# MULTI-STAGE DOCKERFILE FOR RAYZHUB COMPLETE PLATFORM & ENGINE
# ════════════════════════════════════════════════════════════════════════════

# ── STAGE 1: Build Next.js Static Frontend ──
FROM node:20-alpine AS frontend-builder
WORKDIR /app/mmeui

COPY mmeui/package*.json ./
# 💡 FIX: Swapped `npm ci` for `npm install` to handle missing lockfiles
RUN npm install --legacy-peer-deps

COPY mmeui ./
RUN npm run build

# ── STAGE 2: Python FastAPI Server & Production Runtime ──
FROM python:3.11-slim
WORKDIR /app

ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Copy built frontend static export from Stage 1
COPY --from=frontend-builder /app/mmeui/out ./mmeui/out

EXPOSE 8000

CMD ["python", "main.py"]

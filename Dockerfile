# ════════════════════════════════════════════════════════════════════════════
# DOCKERFILE FOR RAYZHUB PRODUCTION PLATFORM & BLAST GATEWAY ADAPTER
# ════════════════════════════════════════════════════════════════════════════

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

EXPOSE 8000

CMD ["python", "main.py"]

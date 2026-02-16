FROM ubuntu:22.04

# Install Python 3.11 and minimal deps on Ubuntu (Playwright needs Ubuntu, not Debian)
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip python3-venv \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies first (Docker layer caching)
COPY requirements.txt .
RUN pip3 install --no-cache-dir --break-system-packages -r requirements.txt

# Install only WebKit browser (--with-deps handles system libraries)
RUN playwright install --with-deps webkit

# Copy application code
COPY app/ app/

ENV INSTANCE_ID=default
ENV MALLOC_ARENA_MAX=4
ENV ALLOWED_DOMAINS="modlix.com,*.modlix.com,sitezump.ai,*.sitezump.ai,adzump.ai,*.adzump.ai"

EXPOSE 6201

VOLUME ["/logs", "/tmp/ehcache"]

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "6201", "--workers", "1", "--log-level", "info"]

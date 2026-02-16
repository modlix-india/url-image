FROM python:3.11-slim

WORKDIR /app

# Install Python dependencies first (Docker layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

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

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Showreel vidéo (backend/services/showreel.py) : Chromium filme l'animation image par image.
# Polices : Montserrat (titres), DejaVu (repli), Noto Color Emoji (pictogrammes).
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
RUN playwright install --with-deps chromium \
    && apt-get update && apt-get install -y --no-install-recommends \
       fonts-montserrat fonts-dejavu-core fonts-noto-color-emoji \
    && rm -rf /var/lib/apt/lists/* \
    && chmod -R a+rX /ms-playwright

# Copy only what the API needs at runtime. Secrets (.env, service account
# JSON, local databases) are excluded by .dockerignore and must come from
# Secret Manager via --set-secrets, never from the build context.
COPY backend/ ./backend/

# Run as an unprivileged user; /app is writable for the SQLite fallback only.
RUN useradd --system --uid 10001 --no-create-home appuser \
    && chown -R appuser /app
USER appuser

EXPOSE 8080

# Single worker avoids SQLite file-locking issues across processes.
# Set DATABASE_URL env var to switch to PostgreSQL for multi-instance deployments.
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "1"]

# ---- Build stage ----
FROM python:3.11-slim AS builder

WORKDIR /build

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ---- Runtime stage ----
FROM python:3.11-slim

ARG VERSION=dev
ARG BUILD_DATE
ARG VCS_REF

LABEL org.opencontainers.image.title="x-postgres-backup" \
    org.opencontainers.image.description="PostgreSQL HA Backup Manager with Web Dashboard" \
    org.opencontainers.image.version="${VERSION}" \
    org.opencontainers.image.created="${BUILD_DATE}" \
    org.opencontainers.image.revision="${VCS_REF}" \
    org.opencontainers.image.source="https://github.com/xdev-asia-labs/x-postgres-backup" \
    org.opencontainers.image.licenses="MIT"

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gnupg2 curl ca-certificates && \
    echo "deb http://apt.postgresql.org/pub/repos/apt bookworm-pgdg main" \
    > /etc/apt/sources.list.d/pgdg.list && \
    curl -fsSL https://www.postgresql.org/media/keys/ACCC4CF8.asc \
    | gpg --dearmor -o /etc/apt/trusted.gpg.d/pgdg.gpg && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
    postgresql-client-18 libpq-dev && \
    apt-get install -y --no-install-recommends postgresql-client-17 || true && \
    apt-get install -y --no-install-recommends postgresql-client-16 || true && \
    apt-get purge -y --auto-remove gnupg2 && \
    rm -rf /var/lib/apt/lists/*

COPY --from=builder /install /usr/local

WORKDIR /app
COPY . .

RUN mkdir -p /data/backups/basebackup /data/backups/pg_dump /data/backups/logs

EXPOSE 8000

ENV BACKUP_DIR=/data/backups \
    DATABASE_URL=postgresql://xpb:xpb@postgres:5432/xpb \
    PG_VERSION=18.3 \
    APP_VERSION=${VERSION}

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

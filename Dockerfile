FROM python:3.11-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    postgresql-client-16 \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /data/backups/basebackup /data/backups/pg_dump /data/backups/logs /data/db

EXPOSE 8000

ENV BACKUP_DIR=/data/backups \
    DATABASE_URL=sqlite:///data/db/backup_manager.db

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

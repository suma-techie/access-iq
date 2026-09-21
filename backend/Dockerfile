FROM python:3.12-slim

WORKDIR /app

# psycopg[binary] and bcrypt ship prebuilt manylinux wheels, so no compiler
# toolchain is needed here — keeps the image small.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Local document/avatar storage does not survive container restarts or
# scaling past one replica — set STORAGE_BACKEND=s3 (see .env.example) for
# any real deployment. This directory only matters for STORAGE_BACKEND=local.
RUN mkdir -p /app/storage/documents

EXPOSE 8000

# Azure App Service for Containers (and most PaaS targets) inject the port
# to listen on via $PORT; default to 8000 for `docker run` / Container Apps.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]

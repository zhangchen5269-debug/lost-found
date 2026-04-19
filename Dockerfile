FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    UPLOAD_DIR=/data/uploads

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential curl \
    && rm -rf /var/lib/apt/lists/*

# 安装依赖
COPY app/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r ./requirements.txt

COPY alembic.ini ./alembic.ini
COPY app ./app/

RUN mkdir -p /data/uploads

EXPOSE 8000

# 启动命令
CMD /bin/sh -c "set -e; cd /app; alembic upgrade head; exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers --forwarded-allow-ips '*' --workers ${UVICORN_WORKERS:-1}"

FROM python:3.12-slim

# 工作区 /app：alembic.ini、依赖清单在此；Python 包在 /app/app/（与 PYTHONPATH 一致）
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

# 依赖层：requirements 放在项目根侧，避免与包目录混淆，也不出现 /app/app/app
COPY app/requirements.txt ./requirements.txt
RUN pip install -r ./requirements.txt

COPY alembic.ini ./alembic.ini
COPY app ./app/

RUN mkdir -p /data/uploads

EXPOSE 8000

# 默认 1 个 worker：与 SQLite 单文件兼容；PostgreSQL 且需提高吞吐时可在 Railway 设置 UVICORN_WORKERS=2
CMD /bin/sh -c "set -e; cd /app; alembic upgrade head; exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers --forwarded-allow-ips='*' --workers ${UVICORN_WORKERS:-1}"

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HOME=/home/studio/.cache/huggingface

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential curl ffmpeg git libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt ./
RUN python -m pip install --upgrade pip \
    && python -m pip install -r requirements.txt

RUN useradd --create-home --uid 10001 studio \
    && mkdir -p /home/studio/.cache/huggingface \
    && chown -R studio:studio /home/studio /app

COPY --chown=studio:studio server.py check-engines.py ./
USER studio

EXPOSE 8790
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=5 \
    CMD curl --fail --silent http://127.0.0.1:8790/live >/dev/null || exit 1

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8790", "--workers", "1", "--proxy-headers", "--forwarded-allow-ips", "*"]

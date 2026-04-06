FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg curl \
    && rm -rf /var/lib/apt/lists/*

COPY deepfake_detector/requirements.txt /app/deepfake_detector/requirements.txt
RUN pip install --no-cache-dir -r /app/deepfake_detector/requirements.txt

COPY . /app

ENV FFMPEG_PATH=/usr/bin/ffmpeg
EXPOSE 8000

CMD ["sh", "-c", "cd /app/deepfake_detector && python -m uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]

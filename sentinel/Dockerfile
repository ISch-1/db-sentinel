FROM python:3.12-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Dependency layer first for build caching.
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY sentinel ./sentinel

EXPOSE 9200

# Run as non-root.
RUN useradd --create-home --uid 10001 sentinel
USER sentinel

ENTRYPOINT ["python", "-m", "sentinel.main"]

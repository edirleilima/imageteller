# syntax=docker/dockerfile:1.7

# ---------- builder stage ----------
FROM python:3.12-slim-bookworm AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# ---------- runtime stage ----------
FROM python:3.12-slim-bookworm AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    HOME=/tmp

# curl is only needed for the healthcheck below.
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Run as a non-root user whose UID/GID matches the OWNER OF THE MOUNTED DATA
# DIRECTORIES on the host, so the container can write images/ and chapters/.
# Defaults to 33:33 (www-data on Debian/Ubuntu hosts). If your host folders are
# owned by a different account, override at build time:
#   docker build --build-arg APP_UID=<uid> --build-arg APP_GID=<gid> -t imageteller-api ./imageteller-api
ARG APP_UID=33
ARG APP_GID=33

COPY --from=builder /opt/venv /opt/venv

WORKDIR /code
# Application code is owned by root and world-readable; the runtime user only
# needs to read/execute it, so no chown is required.
COPY ./app /code/app

USER ${APP_UID}:${APP_GID}

EXPOSE 8001

HEALTHCHECK --interval=300s --timeout=15s --start-period=20s --retries=3 \
    CMD curl --fail --silent http://localhost:8001/imageteller-api/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001", "--workers", "4"]

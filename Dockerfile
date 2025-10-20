# ==========================================
# BUILD STAGE
# ==========================================
FROM python:3.13-slim AS builder

# Build-Dependencies in einem Layer
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc \
        libpq-dev \
        curl \
        git \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /code

COPY pyproject.toml uv.lock ./

# Dependencies + Bytecode Compilation + Cache Cleanup
RUN uv sync --frozen --no-editable --compile-bytecode --no-cache-dir \
    && find /code/.venv -type d -name "__pycache__" -exec rm -rf {} + \
    && rm -rf /root/.cache

COPY . /code

# Playwright + Cleanup
RUN .venv/bin/python -m playwright install chromium \
    && rm -rf /root/.cache/ms-playwright/firefox* \
              /root/.cache/ms-playwright/webkit* \
              /tmp/*

# Build-Dependencies entfernen
RUN apt-get purge -y --auto-remove gcc curl git \
    && rm -rf /var/lib/apt/lists/*

# ==========================================
# FINAL STAGE
# ==========================================
FROM python:3.13-slim

# Runtime-Dependencies (minimal)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libpq5 \
        fonts-liberation \
        libasound2 \
        libatk-bridge2.0-0 \
        libatk1.0-0 \
        libatspi2.0-0 \
        libcairo2 \
        libcups2 \
        libdbus-1-3 \
        libdrm2 \
        libgbm1 \
        libglib2.0-0 \
        libgtk-3-0 \
        libnspr4 \
        libnss3 \
        libpango-1.0-0 \
        libx11-6 \
        libxcb1 \
        libxcomposite1 \
        libxdamage1 \
        libxext6 \
        libxfixes3 \
        libxkbcommon0 \
        libxrandr2 \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Non-root user MIT Home-Directory
RUN groupadd -r appgroup && \
    useradd -r -g appgroup -u 10001 -m -d /home/appuser appuser

WORKDIR /code

COPY --from=builder --chown=appuser:appgroup /code /code

# Create all necessary directories
RUN mkdir -p /code/logs /code/.crawl4ai && \
    chown -R appuser:appgroup /code /home/appuser

ENV PATH="/code/.venv/bin:$PATH" \
    PLAYWRIGHT_BROWSERS_PATH=/code/.venv/lib/python3.13/site-packages/playwright/driver/browsers \
    PYTHONUNBUFFERED=1 \
    CRAWL4AI_BASE_DIRECTORY=/code/.crawl4ai

USER appuser

EXPOSE 8080

CMD ["uvicorn", "src.load_app:app", "--host", "0.0.0.0", "--port", "8080"]

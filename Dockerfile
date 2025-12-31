# ==========================================
# BUILD STAGE
# ==========================================
FROM python:3.13-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev curl git && rm -rf /var/lib/apt/lists/*
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /code
COPY pyproject.toml uv.lock ./

# Dependencies installieren
RUN uv sync --frozen --no-editable --compile-bytecode --no-cache-dir

COPY . /code

# WICHTIG: Wir zwingen Playwright, die Browser IN DAS PROJEKT zu laden
# (anstatt nach /root/.cache, was wir später verlieren würden)
ENV PLAYWRIGHT_BROWSERS_PATH=/code/.venv/lib/python3.13/site-packages/playwright/driver/browsers

# Browser herunterladen (landet jetzt im venv!)
RUN .venv/bin/python -m playwright install chromium

# Cleanup (Firefox/Webkit löschen, um Platz zu sparen)
RUN rm -rf /code/.venv/lib/python3.13/site-packages/playwright/driver/browsers/firefox* \
           /code/.venv/lib/python3.13/site-packages/playwright/driver/browsers/webkit*


# ==========================================
# FINAL STAGE
# ==========================================
FROM python:3.13-slim

# WICHTIG: Auch hier müssen wir Playwright sagen, wo die Browser liegen
ENV PLAYWRIGHT_BROWSERS_PATH=/code/.venv/lib/python3.13/site-packages/playwright/driver/browsers \
    PATH="/code/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    CRAWL4AI_BASE_DIRECTORY=/code/.crawl4ai

WORKDIR /code

# 1. venv kopieren (Da sind jetzt die Browser drin!)
COPY --from=builder /code/.venv /code/.venv

# 2. System-Dependencies installieren
# Wir nutzen den Browser, der jetzt im venv liegt, um die Deps zu ermitteln
RUN apt-get update && \
    /code/.venv/bin/playwright install-deps chromium && \
    apt-get install -y --no-install-recommends libpq5 && \
    rm -rf /var/lib/apt/lists/*

# 3. Rest kopieren
COPY --from=builder /code /code

RUN groupadd -r appgroup && useradd -r -g appgroup -u 10001 -m -d /home/appuser appuser
RUN mkdir -p /code/logs /code/.crawl4ai && chown -R appuser:appgroup /code /home/appuser

USER appuser
EXPOSE 8080
CMD ["uvicorn", "src.load_app:app", "--host", "0.0.0.0", "--port", "8080"]

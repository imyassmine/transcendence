FROM ghcr.io/astral-sh/uv:0.13.7 AS uv
FROM python:3.13-slim

WORKDIR /app
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_PYTHON_DOWNLOADS=never

COPY pyproject.toml uv.lock ./
RUN --mount=from=uv,source=/uv,target=/usr/local/bin/uv \
    uv sync --locked --no-dev --no-install-project
COPY . .

USER 10001:10001
CMD ["uvicorn", "app.router:app", "--host", "0.0.0.0", "--port", "8000"]

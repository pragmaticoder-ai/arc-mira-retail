FROM python:3.11-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY pyproject.toml uv.lock* ./
RUN uv sync --no-dev || uv sync --no-dev --no-frozen

COPY tools/ ./tools/
COPY agents/ ./agents/

ENV PYTHONPATH="/app"
ENV PORT=8080

EXPOSE 8080

CMD ["sh", "-c", "uv run uvicorn agents.pulse.main:app --host 0.0.0.0 --port ${PORT:-8080}"]

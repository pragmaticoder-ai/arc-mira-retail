# tools/Dockerfile — shared container for ARIA + PULSE tool services (SPEC-00 §10)
FROM python:3.11-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Dependency files first (layer caching)
COPY pyproject.toml ./
COPY uv.lock* ./

# Production deps only (no dev group)
RUN uv sync --no-dev || uv sync --no-dev --no-frozen

# Source
COPY tools/ ./tools/

EXPOSE 8080

# AGENT_TYPE is set per Cloud Run deployment: aria or pulse
ARG AGENT_TYPE=aria
ENV AGENT_TYPE=$AGENT_TYPE

CMD ["sh", "-c", "uv run uvicorn tools.${AGENT_TYPE}_tools.main:app --host 0.0.0.0 --port 8080"]

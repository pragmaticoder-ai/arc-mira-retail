FROM python:3.11-slim

# Install uv for fast, reliable package management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Copy dependency specifications
COPY pyproject.toml uv.lock* ./
COPY frontend/pulse-dashboard/requirements.txt ./requirements-dashboard.txt

# Install base dependencies and dashboard dependencies
COPY tools/ ./tools/
COPY agents/ ./agents/
RUN uv sync --frozen --no-dev
RUN uv pip install -r requirements-dashboard.txt

# Copy application source
COPY tools/ ./tools/
COPY frontend/pulse-dashboard/ ./frontend/pulse-dashboard/
COPY frontend/pulse-dashboard/.streamlit/config.toml ./.streamlit/config.toml

ENV PYTHONPATH="/app:/app/frontend/pulse-dashboard"
ENV PORT=8080

EXPOSE 8080

CMD ["/app/.venv/bin/streamlit", "run", "frontend/pulse-dashboard/pulse_dashboard.py", "--server.port=8080", "--server.address=0.0.0.0", "--server.headless=true"]

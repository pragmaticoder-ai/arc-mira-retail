# ARC Backend - Running Locally

Complete guide to run the ARC backend for local development and demo.

## Prerequisites

- Python 3.11+
- `uv` package manager (recommended) or pip
- Docker (optional, for integration tests)

## Quick Start

### 1. Install Dependencies

```bash
# Using uv (recommended - 10-100x faster)
curl -LsSf https://astral.sh/uv/install.sh | sh
uv sync --all-groups

# Or using pip
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Set Environment Variables

Create `.env` file in the project root:

```bash
# Copy the example file
cp .env.example .env
```

Key variables for local development:

```env
# Environment
ENVIRONMENT=development
LOG_LEVEL=INFO

# Mock mode (no GCP needed)
USE_MOCK=true

# Google Cloud (not needed in mock mode)
GOOGLE_CLOUD_PROJECT=mira-arc-hackathon
GOOGLE_CLOUD_REGION=asia-southeast1

# Mock server (optional, for HTTP-based mocks)
MOCK_SERVER_URL=http://localhost:8900
```

### 3. Run ARIA Tools API

```bash
# Using uv
uv run uvicorn tools.aria_tools.main:app --reload --port 8001

# Or using Python directly
python -m uvicorn tools.aria_tools.main:app --reload --port 8001
```

ARIA tools will be available at `http://localhost:8001`

API documentation: `http://localhost:8001/docs`

### 4. Run PULSE Tools API

```bash
# Using uv
uv run uvicorn tools.pulse_tools.main:app --reload --port 8002

# Or using Python directly
python -m uvicorn tools.pulse_tools.main:app --reload --port 8002
```

PULSE tools will be available at `http://localhost:8002`

API documentation: `http://localhost:8002/docs`

### 5. Run Mock Server (Optional)

The mock server provides HTTP endpoints for Google Cloud APIs. Not needed if using in-process mocks (`USE_MOCK=true`).

```bash
cd mocks
uvicorn mock_server:app --port 8900
```

## Testing the APIs

### Health Checks

```bash
# ARIA tools
curl http://localhost:8001/health

# PULSE tools
curl http://localhost:8002/health
```

### Example: Parse Intent

```bash
curl -X POST http://localhost:8001/tools/parse-intent \
  -H "Content-Type: application/json" \
  -d '{"customer_message": "I need weekly halal groceries for family of 4, under AED 300"}'
```

Expected response:

```json
{
  "goal": "weekly groceries",
  "dietary_preference": "halal",
  "budget_aed": 300.0,
  "household_size": 4,
  "urgency": "normal"
}
```

### Example: Build Cart

```bash
curl -X POST http://localhost:8001/tools/build-cart \
  -H "Content-Type: application/json" \
  -d '{
    "goal": "weekly groceries",
    "dietary_preference": "halal",
    "budget_aed": 300,
    "household_size": 4,
    "store_id": "dubai_marina_01"
  }'
```

### Example: Detect Patterns (PULSE)

```bash
curl -X POST http://localhost:8002/tools/detect-patterns \
  -H "Content-Type: application/json" \
  -d '{
    "store_id": "dubai_marina_01",
    "hours": 48,
    "min_incidents": 5
  }'
```

Expected response (demo scenario):

```json
{
  "patterns": [
    {
      "product_id": "rice_brown_500g",
      "product_name": "Brown Rice 500g",
      "store_id": "dubai_marina_01",
      "incident_count": 23,
      "estimated_revenue_lost_aed": 138.00,
      "peak_hour": "10:00-12:00",
      "abandonment_count": 5,
      "evidence": {
        "first_incident": "2026-10-15T13:00:00",
        "last_incident": "2026-10-17T11:00:00",
        "sample_session_ids": ["seed_sess_00", "seed_sess_01", "seed_sess_02"],
        "substitution_acceptance_rate": 0.5
      }
    }
  ]
}
```

## Connecting to aria-app Frontend

The aria-app frontend (Next.js) expects the ARIA agent API at a specific endpoint. Update the frontend environment:

```bash
# In frontend/aria-app/.env.local
ARIA_AGENT_URL=http://localhost:8001
```

Then run the frontend:

```bash
cd frontend/aria-app
npm install
npm run dev
```

The frontend will be available at `http://localhost:3000`

## Running Tests

```bash
# Run all tests
uv run pytest

# Run only unit tests (no Docker needed)
uv run pytest -m unit

# Run integration tests (requires Docker)
uv run pytest -m integration

# Run with coverage
uv run pytest --cov=tools --cov-report=html
```

## Project Structure

```
tools/
├── shared/              # Shared utilities and clients
│   ├── settings.py      # Environment configuration
│   ├── models.py        # Pydantic request/response models
│   ├── logger.py        # Structured logging
│   ├── auth.py          # IAM token verification
│   ├── rate_limit.py    # Rate limiting config
│   ├── alloydb_client.py   # AlloyDB adapter (mock + real)
│   ├── bigquery_client.py  # BigQuery adapter (mock + real)
│   └── mock_inventory.py   # Mock seed data
│
├── aria_tools/          # ARIA CX Agent tools
│   ├── main.py          # FastAPI app
│   ├── parse_intent.py
│   ├── get_customer_context.py
│   ├── build_cart.py
│   ├── check_stock.py
│   ├── suggest_substitution.py
│   ├── optimize_budget.py
│   ├── apply_promotion.py
│   ├── place_order.py
│   └── log_session.py
│
└── pulse_tools/         # PULSE OPS Agent tools
    ├── main.py          # FastAPI app
    ├── detect_patterns.py
    ├── find_root_cause.py
    ├── predict_stockout.py
    ├── calculate_impact.py
    ├── draft_purchase_order.py
    └── execute_perishable_discount.py
```

## Mock Mode

In mock mode (`USE_MOCK=true`), all tools work without any GCP dependencies:

- **AlloyDB**: In-memory data from `mock_inventory.py`
- **BigQuery**: In-memory incidents table with seeded demo data
- **Vertex AI**: Keyword matching instead of Gemini API calls

This enables full end-to-end demo offline:

1. ARIA builds cart, logs session to in-memory BigQuery
2. PULSE reads from same in-memory BigQuery, detects patterns
3. Full ARIA → PULSE loop works locally

## Production Deployment

For production deployment to Google Cloud, see `DEPLOYMENT.md`.

Key changes:
1. Set `USE_MOCK=false`
2. Configure AlloyDB and BigQuery credentials via Secret Manager
3. Deploy to Cloud Run
4. Enable IAM authentication

## Troubleshooting

### Port Already in Use

If ports 8001 or 8002 are already in use:

```bash
# Find process using the port
lsof -i :8001

# Kill the process
kill -9 <PID>

# Or use different ports
uvicorn tools.aria_tools.main:app --port 8003
```

### Import Errors

If you see import errors, ensure you're in the project root and have installed dependencies:

```bash
# Reinstall dependencies
uv sync --all-groups

# Or with pip
pip install -e .
```

### Environment Variables Not Loading

Ensure `.env` file is in the project root (same directory as `pyproject.toml`).

## Demo Flow

The complete demo flow:

1. **Start Backend** (ARIA on port 8001, PULSE on port 8002)
2. **Start Frontend** (aria-app on port 3000)
3. **Demo Scenario**:
   - Sarah chats with ARIA: "Weekly halal groceries, family of 4, AED 300"
   - ARIA builds cart, detects brown rice stockout, suggests basmati substitution
   - Sarah confirms order
   - ARIA logs session to BigQuery bridge
   - Ahmed opens PULSE dashboard
   - PULSE detects brown rice stockout pattern (23 incidents)
   - PULSE shows root cause, drafts PO
   - Ahmed approves PO in one click

The demo is fully functional in mock mode without any GCP deployment.

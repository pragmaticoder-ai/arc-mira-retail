# CONTRIBUTING.md — Developer Guide
> MIRA Retail · ARC v1.0

---

## Local setup

```bash
git clone https://github.com/pragmatic-engineers/arc
cd arc
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements-dev.txt
cp .env.example .env       # fill in your local values
```

---

## Project conventions

### Python
- Python 3.11+
- All tool functions return plain dicts (JSON-serializable)
- All tool functions have a docstring in the exact format shown in `AGENT_CONTRACTS.md`
- Pydantic models in `tools/shared/models.py` for all shared data structures
- Type hints on all function signatures

### Naming
- Tool functions: `snake_case` verbs — `build_cart`, `detect_patterns`, `execute_perishable_discount`
- AlloyDB tables: `snake_case` nouns — `customer_profiles`, `purchase_orders`
- BigQuery tables: `snake_case` nouns — `incidents`, `promotion_log`
- Cloud Run services: `arc-{name}-{type}` — `arc-aria-agent`, `arc-pulse-tools`
- Docker images: `arc-{name}` — `arc-aria`, `arc-pulse`, `arc-tools`, `arc-frontend`

### Git
- Branch naming: `feature/`, `fix/`, `data/`
- Commit messages: imperative mood — "Add suggest_substitution tool" not "Added"
- One PR per tool function — keeps review small and fast
- Never commit `.env` files or service account JSON keys

### Tool function structure
Every tool function follows this pattern:
```python
# tools/aria_tools/build_cart.py

import logging
from tools.shared.alloydb_client import get_connection
from tools.shared.models import CartItem

logger = logging.getLogger(__name__)

def build_cart(
    goal: str,
    dietary_preference: str,
    budget_aed: float,
    household_size: int,
    store_id: str
) -> dict:
    """
    Builds a grocery cart from AlloyDB inventory matching the customer goal.
    Filters by dietary_preference. Selects best-value items within budget_aed.
    Returns items list, total_aed, and items_unavailable list.
    Call after get_customer_context(). Always pass dietary_preference.
    """
    try:
        # implementation
        conn = get_connection()
        # query AlloyDB...
        return {"items": [...], "total_aed": 0.0, "items_unavailable": []}
    except Exception as e:
        logger.error(f"build_cart failed: {e}")
        return {
            "error": True,
            "error_code": "BUILD_CART_ERROR",
            "error_message": str(e),
            "retry_suggested": True
        }
```

---

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific agent tests
pytest tests/test_aria_tools.py -v
pytest tests/test_pulse_tools.py -v
pytest tests/test_bridge.py -v

# Run with coverage
pytest tests/ --cov=tools --cov-report=term-missing
```

### Test data
- Tests use a local SQLite mock (no AlloyDB connection required)
- BigQuery tests use the BigQuery emulator
- See `tests/conftest.py` for fixtures

---

## Frontend development

### ARIA app (Next.js) — your responsibility
```bash
cd frontend/aria-app
npm install
npm run dev
# → open http://localhost:3000
# → set ARIA_AGENT_URL in .env.local to point to local or deployed agent
```

**Stack:** Next.js 14 (App Router), TypeScript, Tailwind CSS
**Key components to build:** NavBar, CategorySidebar, ProductGrid, AriaPanel, ReasoningDrawer, CartContext

### PULSE dashboard (Streamlit) — partner's responsibility
```bash
cd frontend/pulse-dashboard
pip install streamlit
streamlit run pulse_dashboard.py
# → open http://localhost:8501
```

## ADK local development

```bash
# Test ARIA agent interactively
cd agents/aria
adk web .
# → open http://localhost:8000
# → type "Weekly groceries, family of 4, halal, AED 300"
# → observe reasoning chain in the ADK web UI

# Test PULSE agent
cd agents/pulse
adk web .
```

---

## Adding a new tool function

1. Create file in `tools/aria_tools/` or `tools/pulse_tools/`
2. Write the function with a precise docstring (this drives agent reasoning)
3. Add the error response format
4. Register in `agents/aria/tools.py` or `agents/pulse/tools.py`
5. Add to the agent's `FunctionTool` list in `agent.py`
6. Write a test in `tests/`
7. Update `AGENT_CONTRACTS.md` with the new contract

---

*MIRA Retail · ARC v1.0 · Contributing v1.0*

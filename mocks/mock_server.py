"""Standalone HTTP mock server for Google Cloud APIs (ARC backend).

Simulates the external Google endpoints the ARC tools depend on, so the backend
can be developed and demoed with nothing deployed on GCP. The shared adapters
(tools/shared/*) route to this server when MOCK_SERVER_URL is set; otherwise
they run equivalent logic in-process.

Endpoints (shapes approximate the real responses enough for the adapters):
  POST /v1/gemini/generate    -> Vertex AI Gemini text generation
  POST /v1/embeddings         -> Vertex AI text embeddings
  POST /v1/bigquery/query     -> BigQuery query (incidents bridge reads)
  POST /v1/bigquery/insert    -> BigQuery streaming insert (log_session writes)
  GET  /health

Run:
  uvicorn mocks.mock_server:app --port 8900
Then point the backend at it:
  export MOCK_SERVER_URL=http://localhost:8900

This is a MOCK. It does not authenticate, persist to disk, or implement the
full Google API surface — only what the ARC adapters call.
"""

from __future__ import annotations

import hashlib
import uuid
from datetime import datetime

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="ARC Google Cloud Mock Server", version="1.0.0")

# In-memory incidents store so bridge insert -> query works over HTTP too.
_INCIDENTS: dict[str, dict] = {}

ALLOWED_CATEGORIES = [
    "dairy", "grains", "halal_meat", "vegetables",
    "fruits", "beverages", "snacks", "condiments",
]


# ── Gemini ───────────────────────────────────────────────────────────────
class GenerateRequest(BaseModel):
    prompt: str
    model: str | None = None


@app.post("/v1/gemini/generate")
def gemini_generate(req: GenerateRequest) -> dict:
    """Canned Gemini completion. If the prompt looks like a goal-to-category
    classification request, return a plausible category list; otherwise echo."""
    p = req.prompt.lower()
    if "categor" in p or "goal" in p:
        if "biryani" in p:
            cats = ["grains", "halal_meat", "condiments", "vegetables"]
        elif "breakfast" in p:
            cats = ["dairy", "grains", "fruits", "beverages"]
        else:
            cats = ["dairy", "grains", "halal_meat", "vegetables", "fruits", "beverages"]
        return {"text": ",".join(cats), "model": req.model or "gemini-1.5-flash-001", "mock": True}
    return {
        "text": f"[mock-gemini] {req.prompt[:160]}",
        "model": req.model or "gemini-1.5-pro",
        "mock": True,
    }


# ── Embeddings ─────────────────────────────────────────────────────────────
class EmbedRequest(BaseModel):
    text: str
    model: str | None = None
    dim: int = 768


@app.post("/v1/embeddings")
def embeddings(req: EmbedRequest) -> dict:
    """Deterministic pseudo-embedding (same scheme as MockEmbeddings) so
    similarity ordering matches whether mocks run in-process or over HTTP."""
    digest = hashlib.sha256(req.text.lower().encode()).digest()
    vec = [((digest[i % len(digest)] / 255.0) * 2.0) - 1.0 for i in range(req.dim)]
    return {"embedding": vec, "model": req.model or "textembedding-gecko@003", "mock": True}


# ── BigQuery bridge ────────────────────────────────────────────────────────
class BQInsertRequest(BaseModel):
    table: str
    row: dict


@app.post("/v1/bigquery/insert")
def bigquery_insert(req: BQInsertRequest) -> dict:
    """Streaming insert into the mock incidents bridge (idempotent on session_id)."""
    if req.table.endswith("incidents"):
        sid = req.row.get("session_id") or str(uuid.uuid4())
        _INCIDENTS[sid] = {**req.row, "session_id": sid}
        return {"inserted": True, "session_id": sid, "timestamp": datetime.now().isoformat()}
    return {"inserted": True, "timestamp": datetime.now().isoformat()}


class BQQueryRequest(BaseModel):
    kind: str = "incidents"
    store_id: str | None = None


@app.post("/v1/bigquery/query")
def bigquery_query(req: BQQueryRequest) -> dict:
    """Return incidents rows (optionally filtered by store) for PULSE reads."""
    rows = list(_INCIDENTS.values())
    if req.store_id:
        rows = [r for r in rows if r.get("store_id") == req.store_id]
    return {"rows": rows, "row_count": len(rows)}


@app.get("/health")
def health() -> dict:
    return {"status": "healthy", "service": "arc-gcp-mock", "incidents": len(_INCIDENTS)}

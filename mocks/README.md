# ARC mock server — fake Google Cloud APIs

A standalone FastAPI app that simulates the Google endpoints the ARC backend
depends on, so tools can run and demo with nothing on GCP. Optional: the
adapters in `tools/shared/` work fully in-process by default. Use this when you
want a realistic "calling an external API" path.

## Run

```bash
cd mocks
pip install -r requirements.txt
uvicorn mock_server:app --port 8900
# health check: http://localhost:8900/health
```

Then tell the backend to route through it:

```bash
export MOCK_SERVER_URL=http://localhost:8900
```

## Endpoints

| Method | Path | Simulates |
|--------|------|-----------|
| POST | `/v1/gemini/generate` | Vertex AI Gemini text generation |
| POST | `/v1/embeddings` | Vertex AI text embeddings |
| POST | `/v1/bigquery/insert` | BigQuery streaming insert (log_session) |
| POST | `/v1/bigquery/query` | BigQuery query (incidents bridge reads) |
| GET | `/health` | liveness |

## Caveats

This is a mock: no auth, no persistence across restarts, and only the slice of
the Google API surface the ARC adapters actually call. Embedding vectors use the
same deterministic scheme as the in-process mock, so similarity ordering is
identical either way.

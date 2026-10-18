# Optional ARC API simulator

This FastAPI server exposes synthetic generation, embedding and BigQuery-shaped
endpoints for adapter experiments. It is not Google Cloud, a full emulator, or
the shared-storage implementation used by the current local demo.

From the repository root, in a separate terminal:

```bash
uv pip install -r mocks/requirements.txt
.venv/bin/python -m uvicorn mocks.mock_server:app --host 127.0.0.1 --port 8900
```

Set `MOCK_SERVER_URL=http://127.0.0.1:8900` before importing the Python adapters
to exercise HTTP generation/embedding methods. The intent/category heuristics do
not automatically become remote model calls. Real Google integration remains deferred.

| Endpoint | Synthetic purpose | Current adapter routing |
|---|---|---|
| POST /v1/gemini/generate | Canned completion | MockLLM.generate when called with MOCK_SERVER_URL set |
| POST /v1/embeddings | Deterministic product vectors | MockEmbeddings.embed with MOCK_SERVER_URL set |
| POST /v1/bigquery/insert | Simulated insert | Not used by current incident adapters |
| POST /v1/bigquery/query | Simulated query | Not used by current incident adapters |
| GET /health | Liveness | Optional manual check |

The current incident bridge is selected by `ARC_BRIDGE_DB` (SQLite or process
memory), not by MOCK_SERVER_URL. Operational persistence uses ARC_STATE_DB. Use
[scripts/run_local.py](../scripts/run_local.py) for the reproducible complete loop.
The simulator is unauthenticated, synthetic and process-local; it is not a
production endpoint or evidence of live model/BigQuery execution.

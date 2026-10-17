# ARC Mock Server

Standalone HTTP mock server for Google Cloud APIs (ARC backend).

## Purpose

Simulates external Google endpoints the ARC tools depend on, so the backend can be developed and demoed with nothing deployed on GCP.

## Endpoints

The mock server provides these endpoints:

- `POST /v1/gemini/generate` - Vertex AI Gemini text generation
- `POST /v1/embeddings` - Vertex AI text embeddings
- `POST /v1/bigquery/query` - BigQuery query (incidents bridge reads)
- `POST /v1/bigquery/insert` - BigQuery streaming insert (log_session writes)
- `GET /health` - Health check

## Running the Mock Server

```bash
# Install dependencies
pip install fastapi uvicorn pydantic

# Run the server
cd mocks
python mock_server.py

# Or with uvicorn directly:
uvicorn mock_server:app --port 8900
```

## Integration with Backend

Set the `MOCK_SERVER_URL` environment variable to point to the mock server:

```bash
export MOCK_SERVER_URL=http://localhost:8900
```

The shared adapters (`tools/shared/*`) will route to this server when `USE_MOCK=true` (default for development).

## Mock Data

The mock server maintains an in-memory incidents store so bridge insert → query works over HTTP. This enables the ARIA → PULSE flow without real BigQuery.

## Example Usage

```bash
# Health check
curl http://localhost:8900/health

# Simulate Gemini completion
curl -X POST http://localhost:8900/v1/gemini/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "weekly groceries for family of 4"}'

# Insert incident
curl -X POST http://localhost:8900/v1/bigquery/insert \
  -H "Content-Type: application/json" \
  -d '{
    "table": "incidents",
    "row": {
      "session_id": "test-123",
      "customer_id": "sarah_123",
      "store_id": "dubai_marina_01",
      "items_unavailable": [{"product_id": "rice_brown_500g"}]
    }
  }'

# Query incidents
curl -X POST http://localhost:8900/v1/bigquery/query \
  -H "Content-Type: application/json" \
  -d '{"store_id": "dubai_marina_01"}'
```

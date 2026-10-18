# SPEC-ARIA-05 — suggest_substitution

Updated October 18, 2026 · Specification 1.1 · Implemented local behavior

## 1. Purpose and status

Implemented local tool. Processing behavior and limits are specified below.

Google execution/adapters remain deferred. This specification supersedes the
original cloud-first implementation plan for this tool.

## 2. Interfaces

Source: [tools/aria_tools/suggest_substitution.py](../tools/aria_tools/suggest_substitution.py).

```python
suggest_substitution(product_id: str, store_id: str, dietary_preference: str, max_price_aed: float, customer_id: str | None=None) -> dict
```

HTTP request model `SubstitutionRequest`:

- `product_id: str` (required)
- `store_id: str` (required)
- `dietary_preference: str` (required)
- `max_price_aed: float` (required)
- `customer_id: str | None` = `None`

The exact POST route and framework schema are in
[openapi_aria_tools.yaml](openapi_aria_tools.yaml). Python-only arguments
are not implicitly accepted over HTTP.

## 3. Processing behavior

Rank current local inventory with TF-IDF cosine similarity. Hard-filter dietary safety, stock and the caller price ceiling. Prefer a price within ±20% of the original and optionally customer purchase history. Broader price-band fallback remains within the caller ceiling. This tool suggests; explicit feedback controls whether ARIA adds a candidate.

## 4. Validation and limits

Supported diet, positive max_price_aed and an existing original product. Candidate similarity must pass the implemented minimum gate. No candidate returns null and a new/recurring substitution-gap event. Similarity is not an evaluated semantic-equivalence probability.

## 5. Response

substitute_product_id, name, price_aed, similarity_score, reason, in_stock, in_band, out_of_price_range, from_purchase_history, substitution_event. Null candidates keep an explanatory reason.

## 6. Persistence and errors

Use shared adapter interfaces and the storage mode in
[DATA_MODEL.md](../DATA_MODEL.md). Operational state and incidents have separate
transaction boundaries. Tools return the standard error dictionary on business
validation failures; the HTTP wrapper generally retains 200 for that dictionary.
Request-model failures use 422; tool-router auth/rate limits use 401/429.
See [AGENT_CONTRACTS.md](../AGENT_CONTRACTS.md) for the agent-facing error mapping.

## 7. Verification

- Existing `test_aria05*` cases in
  [tests/unit/aria/test_aria_tools.py](../tests/unit/aria/test_aria_tools.py).
- Cross-surface regressions in
  [tests/integration/test_demand_loop.py](../tests/integration/test_demand_loop.py).
- HTTP shape coverage in
  [tests/contract/test_agent_contract.py](../tests/contract/test_agent_contract.py).

These are local tests, not evidence of a deployed Google integration.

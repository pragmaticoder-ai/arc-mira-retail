"""Shared backend adapters for ARC tools.

Every Google-infra dependency sits behind an interface here with a mock
implementation, selected by the USE_MOCK env flag (see settings.py). Tools
import the get_* factories, never the SDKs directly, so swapping mock -> real
GCP is a config change, not a rewrite.

Factories:
  get_alloydb()        -> AlloyDBClient   (customer/inventory/orders/PO)
  get_bigquery()       -> BigQueryClient  (ARIA->PULSE incidents bridge, ML)
  get_llm()            -> LLM             (Gemini reasoning/classification)
  get_embeddings()     -> Embeddings      (product text embeddings)
  get_vector_search()  -> VectorSearch    (AlloyDB AI / ScaNN substitution)
"""

from tools.shared.alloydb_client import get_alloydb
from tools.shared.bigquery_client import get_bigquery
from tools.shared.embeddings import get_embeddings
from tools.shared.llm import get_llm
from tools.shared.settings import settings
from tools.shared.vector_search import get_vector_search

__all__ = [
    "get_alloydb",
    "get_bigquery",
    "get_embeddings",
    "get_llm",
    "get_vector_search",
    "settings",
]

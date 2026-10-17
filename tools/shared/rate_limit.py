"""Rate limiting configuration for ARC tool functions.

Different tools have different rate limits based on their resource usage:
- Lightweight tools (parse_intent): 60/min
- DB-heavy tools (build_cart): 30/min
- Write operations (place_order): 10/min
- BigQuery-heavy tools (detect_patterns): 10/min
"""

from slowapi import Limiter
from slowapi.util import get_remote_address
from tools.shared.settings import settings


limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[f"{settings.rate_limit_per_minute}/minute"]
)


# Per-endpoint rate limits
RATE_LIMITS = {
    # ARIA tools
    "parse_intent": "60/minute",
    "get_customer_context": "60/minute",
    "build_cart": "30/minute",
    "check_stock": "60/minute",
    "suggest_substitution": "30/minute",
    "optimize_budget": "30/minute",
    "apply_promotion": "30/minute",
    "place_order": "10/minute",
    "log_session": "60/minute",
    
    # PULSE tools
    "detect_patterns": "10/minute",
    "find_root_cause": "10/minute",
    "predict_stockout": "10/minute",
    "calculate_impact": "10/minute",
    "draft_purchase_order": "5/minute",
    "execute_perishable_discount": "10/minute",
}

"""Reuse the Google Gen AI transport and ADC credentials within each process."""

from __future__ import annotations

import atexit
from functools import lru_cache

from tools.shared.settings import settings


@lru_cache(maxsize=1)
def get_google_client():
    from google import genai

    client = genai.Client(
        vertexai=True,
        project=settings.google_cloud_project,
        location=settings.vertex_ai_location,
        http_options={"timeout": 60000},
    )
    atexit.register(client.close)
    return client

"""IAM token verification middleware — SPEC-00 §8.

Verifies a Google Cloud IAM Bearer token on every request. In development
(ENVIRONMENT=development, the default) verification is bypassed so the mock
stack runs without credentials.
"""

from __future__ import annotations

from fastapi import HTTPException, Request, status

from tools.shared.settings import settings


async def verify_iam_token(request: Request) -> dict:
    """FastAPI dependency. Returns the token claims, or raises 401.

    Dev bypass: when ENVIRONMENT=development, returns a stub identity without
    checking a token (ARC runs fully mocked locally).
    """
    if settings.environment == "development":
        return {"sub": "dev-user", "email": "dev@mira.ae"}

    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header",
        )

    token = auth_header.split(" ", 1)[1]
    try:
        import google.auth.transport.requests
        import google.oauth2.id_token

        claims = google.oauth2.id_token.verify_oauth2_token(
            token, google.auth.transport.requests.Request()
        )
        return claims
    except Exception as exc:  # noqa: BLE001 - map any verify failure to 401
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        ) from exc

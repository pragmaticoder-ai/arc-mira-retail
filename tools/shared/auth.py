"""IAM token verification middleware for Cloud Run.

In production, all Cloud Run invocations require a valid IAM Bearer token.
In development mode, we bypass verification for local testing.
"""

from __future__ import annotations

from fastapi import Request, HTTPException, status
import google.auth.transport.requests
import google.oauth2.id_token
from tools.shared.settings import settings


async def verify_iam_token(request: Request) -> dict:
    """
    Verify Google Cloud IAM Bearer token on every request.
    
    Returns:
        dict: Decoded token payload
        
    Raises:
        HTTPException: 401 if token is missing or invalid
    """
    # Bypass in development mode
    if settings.environment == "development":
        return {"sub": "dev-user", "email": "dev@mira.ae"}

    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header"
        )

    token = auth_header.split(" ")[1]
    try:
        id_info = google.oauth2.id_token.verify_oauth2_token(
            token,
            google.auth.transport.requests.Request()
        )
        return id_info
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired token: {str(e)}"
        )

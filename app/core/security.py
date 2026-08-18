"""JWT verification using Supabase's JWKS endpoint (ES256 algorithm).

Supabase issues JWTs signed with ECDSA P-256 (ES256). This module:
1. Fetches the JWKS on first use and caches the public key.
2. Verifies incoming Bearer tokens from the Flutter client.
3. Returns the Supabase Auth user ID (sub claim) on success.
"""

import logging
from functools import lru_cache
from typing import Any

import httpx
from jose import JWTError, jwt
from jose.backends import ECKey

from app.core.config import get_settings

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _fetch_jwks() -> dict[str, Any]:
    """Fetch and cache the JWKS from Supabase.

    Uses a synchronous HTTP call at startup time (cached after first call).
    In production, keys rarely rotate, so caching is safe.
    """
    settings = get_settings()
    with httpx.Client(timeout=10.0) as client:
        response = client.get(settings.supabase_jwt_jwks_url)
        response.raise_for_status()
        return response.json()


def _get_public_key() -> ECKey:
    """Extract the EC public key matching our key ID from the JWKS."""
    settings = get_settings()
    jwks = _fetch_jwks()
    for key_data in jwks.get("keys", []):
        if key_data.get("kid") == settings.supabase_jwt_key_id:
            return ECKey(key_data, algorithm="ES256")
    raise ValueError(
        f"Key ID '{settings.supabase_jwt_key_id}' not found in JWKS. "
        "Verify SUPABASE_JWT_KEY_ID in your .env file."
    )


def verify_supabase_token(token: str) -> dict[str, Any]:
    """Verify a Supabase JWT and return its decoded payload.

    Args:
        token: Raw JWT string from the Authorization: Bearer header.

    Returns:
        Decoded JWT payload dictionary.

    Raises:
        JWTError: If the token is invalid, expired, or cannot be verified.
    """
    try:
        public_key = _get_public_key()
        payload = jwt.decode(
            token,
            public_key,
            algorithms=["ES256"],
            options={"verify_aud": False},  # Supabase tokens use 'authenticated' audience
        )
        return payload
    except JWTError as exc:
        logger.warning("JWT verification failed: %s", exc)
        raise


def extract_supabase_user_id(payload: dict[str, Any]) -> str:
    """Extract the Supabase user UUID from the JWT sub claim.

    Args:
        payload: Decoded JWT payload.

    Returns:
        Supabase Auth user ID (UUID string).

    Raises:
        ValueError: If the sub claim is missing.
    """
    user_id = payload.get("sub")
    if not user_id:
        raise ValueError("JWT payload missing 'sub' claim")
    return user_id

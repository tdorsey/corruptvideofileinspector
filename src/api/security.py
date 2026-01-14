"""OIDC security configuration for API authentication."""

import logging
from dataclasses import dataclass
from typing import Any

from authlib.integrations.starlette_client import OAuth
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

logger = logging.getLogger(__name__)

# HTTP Bearer token scheme
security = HTTPBearer()


@dataclass
class OIDCConfig:
    """OIDC configuration."""

    enabled: bool = False
    issuer: str = ""
    client_id: str = ""
    client_secret: str = ""
    audience: str = ""


def get_oidc_config() -> OIDCConfig:
    """Get OIDC configuration from environment or config."""
    import os

    enabled = os.getenv("OIDC_ENABLED", "false").lower() == "true"
    if not enabled:
        logger.info("OIDC authentication is disabled")
        return OIDCConfig(enabled=False)

    config = OIDCConfig(
        enabled=True,
        issuer=os.getenv("OIDC_ISSUER", ""),
        client_id=os.getenv("OIDC_CLIENT_ID", ""),
        client_secret=os.getenv("OIDC_CLIENT_SECRET", ""),
        audience=os.getenv("OIDC_AUDIENCE", ""),
    )

    if not all([config.issuer, config.client_id, config.client_secret]):
        logger.warning(
            "OIDC is enabled but configuration is incomplete. " "Falling back to disabled mode."
        )
        return OIDCConfig(enabled=False)

    logger.info(f"OIDC authentication is enabled with issuer: {config.issuer}")
    return config


def create_oauth_client(oidc_config: OIDCConfig) -> OAuth | None:
    """Create OAuth client for OIDC authentication."""
    if not oidc_config.enabled:
        return None

    oauth = OAuth()
    oauth.register(
        name="oidc",
        client_id=oidc_config.client_id,
        client_secret=oidc_config.client_secret,
        server_metadata_url=f"{oidc_config.issuer}/.well-known/openid-configuration",
        client_kwargs={"scope": "openid profile email"},
    )
    return oauth


async def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict[str, Any]:
    """Verify JWT token from Authorization header.

    This is a placeholder implementation. In production, you should:
    1. Verify the JWT signature using the OIDC provider's public keys
    2. Validate the token expiration, audience, and issuer
    3. Extract and return user claims

    Args:
        credentials: HTTP authorization credentials with bearer token

    Returns:
        User claims from the verified token

    Raises:
        HTTPException: If token is invalid or verification fails
    """
    oidc_config = get_oidc_config()

    # If OIDC is not enabled, allow all requests
    if not oidc_config.enabled:
        return {"sub": "anonymous", "email": "anonymous@localhost"}

    # TODO: Implement proper JWT verification using OIDC provider's public keys
    # For now, this is a placeholder that returns anonymous access
    # In production, use libraries like python-jose or authlib to verify JWTs

    try:
        # Placeholder: In production, decode and verify the JWT token here
        # from authlib.jose import jwt
        # claims = jwt.decode(token, key)
        # Validate claims (iss, aud, exp, etc.)

        logger.warning(
            "Using placeholder token verification. "
            "Implement proper JWT verification for production."
        )
        return {"sub": "authenticated_user", "email": "user@example.com"}

    except Exception as e:
        logger.exception(f"Token verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e


async def get_current_user(
    token_data: dict[str, Any] = Depends(verify_token),
) -> dict[str, Any]:
    """Get current authenticated user from token data.

    Args:
        token_data: Verified token data with user claims

    Returns:
        Current user information
    """
    return token_data

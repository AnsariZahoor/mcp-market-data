"""
Composite Authentication Provider for FastMCP.

Combines multiple authentication methods:
1. API keys for programmatic access (checked first)
2. Privy OAuth for interactive users (fallback)

The provider attempts API key validation first for efficiency,
then falls back to the full OAuth provider if needed.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from starlette.routing import Route

from fastmcp.server.auth import AccessToken
from fastmcp.server.auth.auth import AuthProvider

from ..utils.logging import get_logger

if TYPE_CHECKING:
    from .api_key_verifier import APIKeyVerifier
    from .privy_provider import PrivyProvider

logger = get_logger(__name__)


class CompositeAuthProvider(AuthProvider):
    """
    Composite auth provider that supports both API keys and OAuth.
    
    Authentication flow:
    1. Check if token starts with 'crypto_sk_' (API key prefix)
    2. If yes → validate with APIKeyVerifier
    3. If no → delegate to PrivyProvider
    
    This allows programmatic clients to use simple bearer tokens
    while interactive users go through the full OAuth flow with Privy.
    """

    def __init__(
        self,
        *,
        api_key_verifier: "APIKeyVerifier",
        oauth_provider: "PrivyProvider",
    ):
        """
        Initialize composite auth provider.

        Args:
            api_key_verifier: Verifier for API key tokens
            oauth_provider: Full OAuth provider for interactive users (Privy)
        """
        # Don't require scopes - API keys don't have them
        super().__init__(
            base_url=oauth_provider.base_url,
            required_scopes=[],  # No required scopes for composite auth
        )
        
        self.api_key_verifier = api_key_verifier
        self.oauth_provider = oauth_provider
        
        logger.info("CompositeAuthProvider initialized with API key + Privy OAuth")

    async def verify_token(self, token: str) -> AccessToken | None:
        """
        Verify bearer token: API key first, then Privy OAuth.
        """
        # Strip "Bearer " prefix if present (added by HTTP client)
        if token.startswith("Bearer "):
            token = token[7:]
        
        # API key? → validate directly, skip Privy
        if self.api_key_verifier.is_api_key(token):
            result = await self.api_key_verifier.verify_token(token)
            if result:
                logger.debug(f"✓ API key authenticated: {result.client_id}")
            return result
        
        # Not API key → Privy OAuth
        logger.debug("Token not API key, trying Privy OAuth")
        return await self.oauth_provider.verify_token(token)

    def get_routes(self, mcp_path: str | None = None) -> list[Route]:
        """
        Get routes from Privy OAuth provider.
        
        API keys don't need routes - they use bearer token auth.
        Privy OAuth needs routes for authorization flow, token exchange, etc.
        """
        return self.oauth_provider.get_routes(mcp_path)

    def get_well_known_routes(self, mcp_path: str | None = None) -> list[Route]:
        """Get well-known routes from Privy OAuth provider."""
        return self.oauth_provider.get_well_known_routes(mcp_path)

    def get_middleware(self) -> list:
        """
        Get middleware that calls OUR verify_token (composite).
        
        Important: We need to create BearerAuthBackend with 'self',
        not oauth_provider, so our verify_token is called.
        """
        from mcp.server.auth.middleware.auth_context import AuthContextMiddleware
        from mcp.server.auth.middleware.bearer_auth import BearerAuthBackend
        from starlette.middleware import Middleware
        from starlette.middleware.authentication import AuthenticationMiddleware
        
        return [
            Middleware(
                AuthenticationMiddleware,
                backend=BearerAuthBackend(self),  # Use CompositeAuthProvider, not oauth_provider!
            ),
            Middleware(AuthContextMiddleware),
        ]


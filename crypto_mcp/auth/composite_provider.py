"""
Composite auth: API keys first, then Privy OAuth.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastmcp.server.auth import AccessToken
from fastmcp.server.auth.auth import AuthProvider

from ..utils.logging import get_logger

if TYPE_CHECKING:
    from .api_key_verifier import APIKeyVerifier
    from .privy_provider import PrivyProvider

logger = get_logger(__name__)


class CompositeAuthProvider(AuthProvider):
    def __init__(
        self,
        *,
        api_key_verifier: "APIKeyVerifier",
        oauth_provider: "PrivyProvider",
    ):
        super().__init__(
            base_url=oauth_provider.base_url,
            required_scopes=[],
        )
        self.api_key_verifier = api_key_verifier
        self.oauth_provider = oauth_provider
        logger.info("CompositeAuthProvider initialized with API key + Privy OAuth")

    async def verify_token(self, token: str) -> AccessToken | None:
        if token.startswith("Bearer "):
            token = token[7:]
        if self.api_key_verifier.is_api_key(token):
            result = await self.api_key_verifier.verify_token(token)
            if result:
                logger.debug("API key authenticated: %s", result.client_id)
            return result
        logger.debug("Token not API key, trying Privy OAuth")
        return await self.oauth_provider.verify_token(token)

    def get_routes(self, mcp_path: str | None = None) -> list:
        return self.oauth_provider.get_routes(mcp_path)

    def get_well_known_routes(self, mcp_path: str | None = None) -> list:
        return self.oauth_provider.get_well_known_routes(mcp_path)

    def get_middleware(self) -> list:
        from mcp.server.auth.middleware.auth_context import AuthContextMiddleware
        from mcp.server.auth.middleware.bearer_auth import BearerAuthBackend
        from starlette.middleware import Middleware
        from starlette.middleware.authentication import AuthenticationMiddleware

        return [
            Middleware(
                AuthenticationMiddleware,
                backend=BearerAuthBackend(self),
            ),
            Middleware(AuthContextMiddleware),
        ]

"""
API Key Verifier for Crypto MCP.
Set via env: CRYPTO_MCP_API_KEY=crypto_sk_...
"""
from typing import Any

from fastmcp.server.auth import AccessToken, TokenVerifier

from ..utils.config import CRYPTO_MCP_API_KEY
from ..utils.logging import get_logger

logger = get_logger(__name__)

API_KEY_PREFIX = "crypto_sk_"


def load_api_key_from_config() -> dict[str, dict[str, Any]]:
    if not CRYPTO_MCP_API_KEY:
        return {}
    return {CRYPTO_MCP_API_KEY: {}}


class APIKeyVerifier(TokenVerifier):
    def __init__(self, keys: dict[str, dict[str, Any]] | None = None):
        super().__init__()
        self.keys = keys if keys is not None else load_api_key_from_config()
        if self.keys:
            logger.info("APIKeyVerifier loaded %s key(s)", len(self.keys))

    def is_api_key(self, token: str) -> bool:
        return token.startswith(API_KEY_PREFIX)

    async def verify_token(self, token: str) -> AccessToken | None:
        if not self.is_api_key(token):
            return None
        if token not in self.keys:
            return None
        key_id = token[len(API_KEY_PREFIX) :][:12]
        logger.info("API key authenticated: %s...", key_id)
        return AccessToken(
            token=token,
            client_id=f"api_key:{key_id}",
            scopes=[],
            claims={"sub": f"api_key:{key_id}", "type": "api_key"},
        )

"""
Simple API Key Verifier for FastMCP.

Set API key via environment variable:
  CRYPTO_MCP_API_KEY=crypto_sk_abc123
"""
from typing import Any

from fastmcp.server.auth import AccessToken, TokenVerifier

from ..utils.config import CRYPTO_MCP_API_KEY
from ..utils.logging import get_logger

logger = get_logger(__name__)

API_KEY_PREFIX = "crypto_sk_"


def load_api_key_from_config() -> dict[str, dict[str, Any]]:
    """Load API key from config."""
    if not CRYPTO_MCP_API_KEY:
        return {}
    
    return {CRYPTO_MCP_API_KEY: {}}


class APIKeyVerifier(TokenVerifier):
    """
    Simple API key verifier.
    
    Validates tokens starting with 'crypto_sk_' against a dict of valid keys.
    Keys are loaded from environment or passed directly.
    """

    def __init__(
        self,
        keys: dict[str, dict[str, Any]] | None = None,
    ):
        """
        Initialize API key verifier.

        Args:
            keys: Dict of {api_key: metadata}. If None, loads from env.
        """
        super().__init__()
        self.keys = keys if keys is not None else load_api_key_from_config()
        
        if self.keys:
            logger.info(f"APIKeyVerifier loaded {len(self.keys)} key(s)")

    def is_api_key(self, token: str) -> bool:
        """Check if token is an API key."""
        return token.startswith(API_KEY_PREFIX)

    async def verify_token(self, token: str) -> AccessToken | None:
        """Verify API key and return AccessToken if valid."""        
        if not self.is_api_key(token):
            return None

        if token not in self.keys:
            logger.debug("API key not found")
            return None

        # Build identifier from key (first 12 chars after prefix)
        key_id = token[len(API_KEY_PREFIX):][:12]
        
        logger.info(f"✓ API key authenticated: {key_id}...")
        
        return AccessToken(
            token=token,
            client_id=f"api_key:{key_id}",
            scopes=[],
            claims={
                "sub": f"api_key:{key_id}",
                "type": "api_key",
            },
        )

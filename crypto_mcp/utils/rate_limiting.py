"""
Rate limiting utilities for FastMCP server.

Provides client identification functions for per-user rate limiting.
Supports both API keys and Discord OAuth tokens.
"""

from fastmcp.server.dependencies import get_access_token
from .logging import get_logger

logger = get_logger(__name__)


def get_client_identifier(context):
    """
    Extract client identifier for per-user rate limiting.
    
    Supports both authentication methods:
    - API keys: Uses "api_key:<key_id>" as identifier
    - Discord OAuth: Uses Discord user ID as identifier
    
    Args:
        context: MiddlewareContext from FastMCP middleware
        
    Returns:
        str: Client identifier (API key ID or Discord user ID)
        
    Note:
        Auth is required, so this should always return a valid identifier.
        The token is validated by FastMCP's auth middleware before reaching here.
    """
    try:
        token = get_access_token()
        if token and hasattr(token, 'claims') and token.claims:
            logger.info(f"Rate limiting: token claims = {token.claims}")
            logger.info(f"Rate limiting: token client_id = {token.client_id}")
            auth_type = token.claims.get("type", "oauth")
            client_id = token.claims.get("sub") or token.claims.get("privy_did") or token.client_id
            
            if client_id:
                if auth_type == "api_key":
                    logger.debug(f"Rate limiting: API key {client_id}")
                else:
                    logger.debug(f"Rate limiting: Privy user {client_id}")
                return client_id
            
        # This should never happen if auth is properly configured
        logger.error("Rate limiting: Token exists but has no 'sub' claim. Claims: %s", token.claims if token else "no token")
        raise ValueError("Invalid token: missing 'sub' claim")
        
    except Exception as e:
        # This should never happen if auth middleware is working
        logger.error(f"Rate limiting: Failed to get access token: {e}")
        raise RuntimeError(f"Authentication required: {e}") from e


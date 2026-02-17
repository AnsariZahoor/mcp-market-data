"""
Crypto MCP Server
A Model Context Protocol server for cryptocurrency exchange data
Supports Binance, Bybit, and Hyperliquid

Authentication:
- API keys (crypto_sk_*) for programmatic access
- Privy OAuth for interactive users
"""
import time
from fastmcp import FastMCP
from starlette.responses import JSONResponse
from fastmcp.server.dependencies import get_access_token
from fastmcp.server.middleware.rate_limiting import RateLimitingMiddleware

from cryptography.fernet import Fernet
from key_value.aio.stores.redis import RedisStore
from key_value.aio.wrappers.encryption import FernetEncryptionWrapper

from .auth import APIKeyVerifier, PrivyProvider, CompositeAuthProvider

from .utils.logging import configure_logging, get_logger
from .tools.trading import get_trading_pairs, list_supported_exchanges
from .tools.market_data import get_klines
from .tools.derivatives import get_funding_rate, get_open_interest
from .tools.hyperliquid import get_hyperliquid_live_market_data
from .tools.indicators import calculate_indicator
from .resources.market import register_market_resources
from .resources.metrics import register_metrics_resources
from .utils.rate_limiting import get_client_identifier
from .utils.config import (
    MCP_SERVER_NAME,
    MCP_SERVER_INSTRUCTIONS,
    BASE_URL,
    LOCAL_TEST,
    REDIS_HOST,
    JWT_SIGNING_KEY,
    STORAGE_ENCRYPTION_KEY,
    RATE_LIMIT_RPS,
    RATE_LIMIT_BURST,
)

configure_logging()
logger = get_logger(__name__)
logger.info("Crypto MCP Server starting up...")

auth_provider = None
if not LOCAL_TEST:
    if not JWT_SIGNING_KEY or not STORAGE_ENCRYPTION_KEY:
        raise ValueError(
            "Production mode requires JWT_SIGNING_KEY and STORAGE_ENCRYPTION_KEY"
        )
    if not REDIS_HOST:
        raise ValueError("Production mode requires REDIS_HOST")
    logger.info("Configuring API keys + Privy OAuth")

    encrypted_storage = FernetEncryptionWrapper(
        key_value=RedisStore(host=REDIS_HOST, port=6379),
        fernet=Fernet(STORAGE_ENCRYPTION_KEY),
    )
    api_key_verifier = APIKeyVerifier()
    privy_provider = PrivyProvider(
        base_url=BASE_URL,
        jwt_signing_key=JWT_SIGNING_KEY,
        client_storage=encrypted_storage,
        require_authorization_consent=False,
    )
    auth_provider = CompositeAuthProvider(
        api_key_verifier=api_key_verifier,
        oauth_provider=privy_provider,
    )
else:
    logger.info("Local development mode: authentication DISABLED")

mcp_config = {"name": MCP_SERVER_NAME, "instructions": MCP_SERVER_INSTRUCTIONS}
if auth_provider:
    mcp_config["auth"] = auth_provider

mcp = FastMCP(**mcp_config)

mcp.add_middleware(RateLimitingMiddleware(
        max_requests_per_second=RATE_LIMIT_RPS,
        burst_capacity=RATE_LIMIT_BURST,
        get_client_id=get_client_identifier,  # Enable per-user rate limiting
        global_limit=False,  # Per-user, not global
))
logger.info(f"✅ Rate limiting middleware configured: {RATE_LIMIT_RPS} req/sec sustained, {RATE_LIMIT_BURST} burst capacity")

mcp.tool(get_trading_pairs)
mcp.tool(list_supported_exchanges)
mcp.tool(get_hyperliquid_live_market_data)
mcp.tool(get_klines)
mcp.tool(get_funding_rate)
mcp.tool(get_open_interest)
mcp.tool(calculate_indicator)
register_market_resources(mcp)
register_metrics_resources(mcp)


@mcp.custom_route("/health", methods=["GET"])
async def health_check(request):
    return JSONResponse({"status": "healthy", "service": "crypto-mcp-server"})


# Add a protected tool to test authentication
@mcp.tool
async def get_user_info() -> dict:
    """Returns information about the authenticated user (Privy or API key)."""
    token = get_access_token()
    
    auth_type = token.claims.get("type", "unknown")
    
    if auth_type == "api_key":
        return {
            "auth_type": "api_key",
            "client_id": token.claims.get("sub"),
        }
    elif auth_type == "privy":
        return {
            "auth_type": "privy",
            "user_id": token.claims.get("sub"),
            "email": token.claims.get("email"),
            "privy_did": token.claims.get("privy_did"),
        }
    else:
        return {
            "auth_type": auth_type,
            "claims": token.claims,
        }

# Add a simple test tool to verify rate limiting
@mcp.tool
async def test_rate_limit() -> dict:
    """Simple test tool to verify rate limiting is working. Returns success message."""
    return {
        "status": "success",
        "message": "Rate limiting test tool executed successfully",
        "timestamp": time.time()
    }


# Add a protected tool to test authentication
# @mcp.tool
# async def get_token_info() -> dict:
#     """Returns information about the Auth0 token."""
#     from fastmcp.server.dependencies import get_access_token

#     token = get_access_token()

#     return {
#         "issuer": token.claims.get("iss"),
#         "audience": token.claims.get("aud"),
#         "scope": token.claims.get("scope")
#     }

app = mcp.http_app()


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()

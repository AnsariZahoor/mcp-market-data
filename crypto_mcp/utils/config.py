"""
Configuration module for Crypto MCP Server
Centralizes all environment variable access
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Auth & server
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
LOCAL_TEST = os.getenv("LOCAL_TEST", "false").lower() in ("true", "1", "yes")
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
JWT_SIGNING_KEY = os.getenv("JWT_SIGNING_KEY")
STORAGE_ENCRYPTION_KEY = os.getenv("STORAGE_ENCRYPTION_KEY")
CRYPTO_MCP_API_KEY = os.getenv("CRYPTO_MCP_API_KEY")
RATE_LIMIT_RPS = int(os.getenv("MCP_RATE_LIMIT_RPS", 10)) # Rate limit requests per second
RATE_LIMIT_BURST = int(os.getenv("MCP_RATE_LIMIT_BURST", 20)) # Rate limit burst requests

# MCP Server Configuration
MCP_SERVER_NAME = "CryptoMCP"
MCP_SERVER_INSTRUCTIONS = (
    "You are CryptoMCP: a crypto market-data agent for Binance, Bybit, and Hyperliquid.\n"
    "Use this server for exchange discovery, OHLCV candles, derivatives data, and technical indicators.\n\n"
    "**Always start with discovery (avoid invalid symbols/params):**\n"
    "- Symbols/markets: `exchange://list`, `exchange://{exchange}/{market}/active` (or `get_trading_pairs`)\n"
    "- Metric meanings + required params: `metrics://market_data`\n\n"
    "**Tools:**\n"
    "- Discovery: `list_supported_exchanges`, `get_trading_pairs`\n"
    "- OHLCV: `get_klines`\n"
    "- Derivatives: `get_funding_rate`, `get_open_interest`\n"
    "- Hyperliquid (live snapshot): `get_hyperliquid_live_market_data`\n"
    "- Indicators: `calculate_indicator`\n\n"
    "**Critical gotchas:**\n"
    "- Timestamp units:\n"
    "  - `get_klines` / `get_funding_rate` / `get_open_interest`: **milliseconds**\n"
    "- Hyperliquid: **LIVE ONLY** here; symbol is base asset (e.g., `BTC`) and there are no historical klines.\n"
    "- Interval formats: Binance uses `1h`/`4h`/`1d`; Bybit uses `60`/`240`/`D`.\n"
    "- For \"current/latest/now\": keep `limit` small.\n\n"
    "**Supported exchanges**: Binance, Bybit, Hyperliquid (spot & futures)."
)

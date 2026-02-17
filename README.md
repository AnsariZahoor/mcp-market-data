# Crypto MCP Server

A production-ready **Model Context Protocol (MCP)** server that exposes cryptocurrency exchange market data to AI agents. Supports Binance, Bybit, and Hyperliquid for spot & futures markets.

---

## Authentication

Custom **Privy**-based authentication out of the box, with a pluggable auth layer so you can swap in API keys, OAuth, or other providers.

**Why Privy?** Many organizations already use Privy for wallet and social login. This setup provides a **single authentication layer** across the stack—no duplicate auth flows when integrating with existing org infra.

A separate **Privy Login** page (`privy-login-app/`) is built in **Next.js**. Users sign in there and obtain tokens for accessing the MCP server. The auth flow is decoupled so the login UI can be customized or replaced without touching the MCP backend.

---

## Features

| Capability | Exchanges | Description |
|------------|-----------|-------------|
| **Exchange Discovery** | All | Trading pairs, supported markets, active/inactive filters |
| **OHLCV Klines** | Binance, Bybit | Historical candlestick data with flexible intervals |
| **Funding Rate** | Binance, Bybit | Perpetual contract funding rate history |
| **Open Interest** | Binance, Bybit | OI history with configurable periods |
| **Hyperliquid Live** | Hyperliquid | Real-time market snapshots (no historical candles) |
| **Technical Indicators** | Binance, Bybit | RSI, MACD, SMA, EMA, BB, ATR, STOCH, CCI, OBV, VWAP, MFI, KC |

---

## Architecture

```
mcp-market-data/
├── crypto_mcp/            # MCP server (Python)
├── privy-login-app/       # Privy login UI (Next.js)
├── docker/                # Dockerfiles
└── docker-compose.yml

crypto_mcp/
├── server.py              # FastMCP app, tool registration, health route
├── core/
│   ├── base_exchange.py   # Abstract base + HTTP/2 connection pooling, retries
│   ├── exchange_factory.py
│   └── errors.py          # Structured error codes
├── exchanges/             # Binance, Bybit, Hyperliquid adapters
├── tools/                 # MCP tools (klines, funding, OI, indicators, etc.)
├── resources/             # MCP resources (metrics catalog, exchange metadata)
└── utils/                 # Config, logging, TechnicalIndicators
```

**Production considerations:**
- **Connection pooling** — shared `httpx.Client` with HTTP/2, 30 keepalive, 100 max connections
- **Retries** — tenacity with exponential backoff (3 attempts)
- **Validation** — Pydantic models for all tool inputs, sanitized symbols/intervals
- **Error responses** — structured `success`, `error_type`, `error_message`, `meta`
- **Metric catalog** — `metrics://market_data` resource for AI agents to discover param formats (units, intervals, exchange quirks)

---

## Quick Start

```bash
# Install (example; adjust to your env)
pip install fastmcp httpx pydantic tenacity python-dotenv pandas pandas-ta

# Run
python -m crypto_mcp.server
# or
uvicorn crypto_mcp.server:app --host 0.0.0.0 --port 8000
```

**Health check:**
```bash
curl http://localhost:8000/health
# {"status":"healthy","service":"crypto-mcp-server"}
```

---

## Docker

All services are containerized via Docker Compose:

| Service | Port | Description |
|---------|------|-------------|
| `redis` | 6379 | OAuth token storage |
| `crypto-mcp` | 8000 | MCP server |
| `privy-login` | 3000 | Next.js login app |

```bash
docker compose up -d
```

Copy `.env.example` to `.env` and fill in your values. Health checks and Redis readiness ensure correct startup order.

---

## MCP Tools

| Tool | Purpose |
|------|---------|
| `list_supported_exchanges` | List exchanges and their markets |
| `get_trading_pairs` | Discovery: active/inactive pairs per exchange & market |
| `get_klines` | OHLCV candles (symbol, interval, market, time range) |
| `get_funding_rate` | Funding rate history |
| `get_open_interest` | Open interest history |
| `get_hyperliquid_live_market_data` | Live snapshot for Hyperliquid |
| `calculate_indicator` | Technical indicator from klines |

---

## MCP Resources

- `metrics://index` — Catalog index
- `metrics://market_data` — Input-format notes (ms timestamps, interval formats, exchange quirks)
- `exchange://list` — Supported exchanges
- `exchange://{exchange}/{market}/active` — Active pairs
- `exchange://{exchange}/{market}/inactive` — Inactive pairs

---

## Exchange Notes

| Exchange | Klines | Funding/OI | Intervals |
|----------|--------|------------|-----------|
| Binance | ✅ | ✅ | `1m`, `5m`, `1h`, `4h`, `1d`, ... |
| Bybit | ✅ | ✅ | `60`, `240`, `D`, `W`, `M` |
| Hyperliquid | Live only | — | Use `get_hyperliquid_live_market_data` |

**Timestamps:** All time params (`start_time`, `end_time`) are **milliseconds**.

---

## Author

Zahoor · MIT License

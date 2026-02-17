from typing import Literal, Optional, List, Dict, Any
from pydantic import BaseModel, Field, ValidationError, field_validator
import httpx
from ..core.exchange_factory import ExchangeFactory
from ..core.errors import ErrorCode

class HyperliquidLiveInput(BaseModel):
    exchange: Literal["hyperliquid"] = Field(..., description="Must be 'hyperliquid'.")
    symbol: Optional[str] = Field(None, description="Optional symbol filter (e.g., 'BTC').")

    @field_validator('symbol')
    @classmethod
    def sanitize_symbol(cls, v: Optional[str]) -> Optional[str]:
        if v:
            return v.strip().upper()
        return v

def get_hyperliquid_live_market_data(
    exchange: Literal["hyperliquid"],
    symbol: Optional[str] = None,
    
    sessionId: Optional[str] = None,
    action: Optional[str] = None,
    chatInput: Optional[str] = None,
    toolCallId: Optional[str] = None
) -> dict:
    """
    Fetch Hyperliquid LIVE-ONLY market snapshots (no historical candles).

    **Metric catalog**
    - Input-format notes: see `metrics://market_data`

    **Core constraints**
    - This tool returns **real-time snapshots only** (no historical OHLCV on Hyperliquid here).
    - Symbol format is **base asset** (e.g., `BTC`, `ETH`, `SOL`) — not `BTCUSDT`.
    - If `symbol` is omitted: returns **all** markets.
    - Invalid `symbol` returns `{count: 0, markets: []}` with `success=true`.

    **When to use something else**
    - Historical candles: `get_klines` (Binance/Bybit only)
    - Historical funding/OI: `get_funding_rate` / `get_open_interest` (Binance/Bybit only)

    Returns:
        {
          "success": bool,
          "data": {
            "exchange": "hyperliquid",
            "symbol_filter": str | None,
            "count": int,
            "markets": [...]
          },
          "meta": {"data_type": "live", "timestamp": "realtime"}
        }

    Examples:
        # All markets
        get_hyperliquid_live_market_data(exchange="hyperliquid")

        # One market
        get_hyperliquid_live_market_data(exchange="hyperliquid", symbol="BTC")
    """
    try:
        input_data = HyperliquidLiveInput(exchange=exchange, symbol=symbol)
        
        with ExchangeFactory.create(input_data.exchange) as exchange_instance:
            if not hasattr(exchange_instance, 'fetch_market_data'):
                raise NotImplementedError(f"Exchange '{input_data.exchange}' does not support live market data")
            
            data = exchange_instance.fetch_market_data(symbol=input_data.symbol)
            
            return {
                "success": True,
                "data": {
                    "exchange": input_data.exchange,
                    "symbol_filter": input_data.symbol,
                    "count": len(data),
                    "markets": data
                },
                "error_type": None,
                "error_message": None,
                "meta": {
                    "data_type": "live",
                    "timestamp": "realtime"
                }
            }

    except ValidationError as e:
        return {
            "success": False,
            "data": None,
            "error_type": ErrorCode.VALIDATION_ERROR,
            "error_message": str(e),
            "meta": {"exchange": exchange, "symbol": symbol}
        }
    except ValueError as e:
        return {
            "success": False,
            "data": None,
            "error_type": ErrorCode.INVALID_PARAMETER,
            "error_message": str(e),
            "meta": {"exchange": exchange, "symbol": symbol}
        }
    except httpx.HTTPError as e:
        return {
            "success": False,
            "data": None,
            "error_type": ErrorCode.API_ERROR,
            "error_message": str(e),
            "meta": {"exchange": exchange, "symbol": symbol}
        }
    except Exception as e:
        return {
            "success": False,
            "data": None,
            "error_type": ErrorCode.UNKNOWN_ERROR,
            "error_message": str(e),
            "meta": {"exchange": exchange, "symbol": symbol}
        }

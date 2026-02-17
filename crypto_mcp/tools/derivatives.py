from typing import Literal, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, ValidationError, field_validator
import httpx
from ..core.exchange_factory import ExchangeFactory
from ..core.errors import ErrorCode

# --- Tool 1: Funding Rate ---

class FundingRateInput(BaseModel):
    exchange: Literal["binance", "bybit"] = Field(..., description="Exchange name.")
    symbol: str = Field(..., description="Symbol (e.g., 'BTCUSDT', 'ETHUSDT', 'XRPUSDT').")
    start_time: Optional[int] = Field(None, description="Start time (ms).")
    end_time: Optional[int] = Field(None, description="End time (ms).")
    limit: int = Field(100, ge=1, description="Number of records.")

    @field_validator('symbol')
    @classmethod
    def sanitize_symbol(cls, v: str) -> str:
        return v.strip().upper()
    
    @field_validator('start_time', 'end_time', mode='before')
    @classmethod
    def convert_timestamp(cls, v):
        """Convert string timestamps to int if needed."""
        if v is None:
            return None
        if isinstance(v, str):
            return int(v)
        return v

def get_funding_rate(
    exchange: Literal["binance", "bybit"],
    symbol: str,
    limit: int = 100,
    start_time: Optional[Union[int, str]] = None,
    end_time: Optional[Union[int, str]] = None,

    sessionId: Optional[str] = None,
    action: Optional[str] = None,
    chatInput: Optional[str] = None,
    toolCallId: Optional[str] = None
) -> dict:
    """
    Fetch funding rate history for a perpetual contract.

    **Metric catalog**
    - Input-format notes: see `metrics://market_data`

    **Units**
    - `start_time` / `end_time` are **milliseconds** (not seconds).

    **Exchanges**
    - `binance`, `bybit`

    **Rules / gotchas**
    - Symbol is auto-uppercased (e.g., `btcusdt` → `BTCUSDT`).
    - Limits are capped: Binance max 1000, Bybit max 200.
    - Bybit time range requires **both** `start_time` and `end_time` (can’t pass only start).

    **For “latest/current”**
    - Use `limit=1` and omit `start_time`/`end_time`.

    Returns:
        {
          "success": bool,
          "data": {
            "exchange": "binance" | "bybit",
            "datatype": "funding_rate",
            "symbol_filter": str,
            "count": int,
            "funding_rates": [...]
          }
        }

    Examples:
        # Latest funding rate
        get_funding_rate(exchange="binance", symbol="BTCUSDT", limit=1)

        # Time range (ms)
        get_funding_rate(exchange="binance", symbol="BTCUSDT", start_time=1766000000000, end_time=1766160000000, limit=50)
    """
    try:
        # Convert string timestamps to int if provided (MCP interface may pass strings)
        if start_time is not None and isinstance(start_time, str):
            start_time = int(start_time)
        if end_time is not None and isinstance(end_time, str):
            end_time = int(end_time)
        
        input_data = FundingRateInput(exchange=exchange, symbol=symbol, limit=limit, start_time=start_time, end_time=end_time)
        
        with ExchangeFactory.create(input_data.exchange) as exchange_instance:
            # Apply exchange limit rules
            limit_val = min(input_data.limit, 1000 if input_data.exchange == "binance" else 200)
            
            if not hasattr(exchange_instance, 'fetch_funding_rate'):
                raise NotImplementedError(f"Exchange '{input_data.exchange}' does not support funding rate")
            
            data = exchange_instance.fetch_funding_rate(
                symbol=input_data.symbol,
                start_time=input_data.start_time,
                end_time=input_data.end_time,
                limit=limit_val
            )
            
            return {
                "success": True,
                "data": {
                    "exchange": input_data.exchange,
                    "datatype": "funding_rate",
                    "symbol_filter": input_data.symbol,
                    "count": len(data),
                    "funding_rates": data
                }
            }
    except ValidationError as e:
        return {
            "success": False,
            "error_type": ErrorCode.VALIDATION_ERROR,
            "error_message": str(e),
            "meta": {"exchange": exchange, "symbol": symbol}
        }
    except ValueError as e:
        return {
            "success": False,
            "error_type": ErrorCode.INVALID_PARAMETER,
            "error_message": str(e),
            "meta": {"exchange": exchange, "symbol": symbol}
        }
    except httpx.HTTPError as e:
        return {
            "success": False,
            "error_type": ErrorCode.API_ERROR,
            "error_message": str(e),
            "meta": {"exchange": exchange, "symbol": symbol}
        }
    except NotImplementedError as e:
        return {
            "success": False,
            "error_type": ErrorCode.NOT_IMPLEMENTED,
            "error_message": str(e),
            "meta": {"exchange": exchange, "symbol": symbol}
        }
    except Exception as e:
        return {
            "success": False,
            "error_type": ErrorCode.UNKNOWN_ERROR,
            "error_message": str(e),
            "meta": {"exchange": exchange, "symbol": symbol}
        }

# --- Tool 2: Open Interest ---

class OpenInterestInput(BaseModel):
    exchange: Literal["binance", "bybit"] = Field(..., description="Exchange name.")
    symbol: str = Field(..., description="Symbol (e.g., 'BTCUSDT', 'ETHUSDT', 'XRPUSDT').")
    period: str = Field(..., description="Time period (e.g., '1h', '4h').")
    limit: int = Field(100, ge=1, description="Number of records.")
    start_time: Optional[int] = Field(None, description="Start time (ms).")
    end_time: Optional[int] = Field(None, description="End time (ms).")

    @field_validator('symbol')
    @classmethod
    def sanitize_symbol(cls, v: str) -> str:
        return v.strip().upper()

    @field_validator('period')
    @classmethod
    def sanitize_period(cls, v: str) -> str:
        return v.strip().lower()
    
    @field_validator('start_time', 'end_time', mode='before')
    @classmethod
    def convert_timestamp(cls, v):
        """Convert string timestamps to int if needed."""
        if v is None:
            return None
        if isinstance(v, str):
            return int(v)
        return v

def get_open_interest(
    exchange: Literal["binance", "bybit"],
    symbol: str,
    period: str,
    limit: int = 100,
    start_time: Optional[Union[int, str]] = None,
    end_time: Optional[Union[int, str]] = None,

    sessionId: Optional[str] = None,
    action: Optional[str] = None,
    chatInput: Optional[str] = None,
    toolCallId: Optional[str] = None
) -> dict:
    """
    Fetch open interest (OI) history for a perpetual contract.

    **Metric catalog**
    - Input-format notes: see `metrics://market_data`

    **Units**
    - `start_time` / `end_time` are **milliseconds** (not seconds).

    **Exchanges**
    - `binance`, `bybit`

    **Supported periods** (auto-lowercased)
    - `5m`, `15m`, `30m`, `1h`, `4h`, `1d`

    **Rules / gotchas**
    - Symbol is auto-uppercased (e.g., `btcusdt` → `BTCUSDT`).
    - Limits are capped: Binance max 500, Bybit max 200.
    - Bybit time range requires **both** `start_time` and `end_time`.

    **For “latest/current”**
    - Use `limit=1` and omit `start_time`/`end_time`.

    Returns:
        {
          "success": bool,
          "data": {
            "exchange": "binance" | "bybit",
            "datatype": "open_interest",
            "symbol": str,
            "period": str,
            "count": int,
            "history": [...]
          }
        }

    Examples:
        # Latest OI
        get_open_interest(exchange="binance", symbol="BTCUSDT", period="1h", limit=1)

        # Time range (ms)
        get_open_interest(exchange="binance", symbol="BTCUSDT", period="1h", start_time=1766000000000, end_time=1766160000000, limit=50)
    """
    try:
        # Convert string timestamps to int if provided (MCP interface may pass strings)
        if start_time is not None and isinstance(start_time, str):
            start_time = int(start_time)
        if end_time is not None and isinstance(end_time, str):
            end_time = int(end_time)
        
        input_data = OpenInterestInput(exchange=exchange, symbol=symbol, period=period, limit=limit, start_time=start_time, end_time=end_time)
        
        with ExchangeFactory.create(input_data.exchange) as exchange_instance:
            # Apply exchange limit rules
            limit_val = min(input_data.limit, 500 if input_data.exchange == "binance" else 200)
            
            if input_data.exchange == "bybit":
                interval_map = {"5m": "5min", "15m": "15min", "30m": "30min", "1h": "1h", "4h": "4h", "1d": "1d"}
                interval = interval_map.get(input_data.period, input_data.period)
                data = exchange_instance.fetch_open_interest(
                    symbol=input_data.symbol,
                    interval=interval,
                    limit=limit_val,
                    start_time=input_data.start_time,
                    end_time=input_data.end_time
                )
            else:
                if not hasattr(exchange_instance, 'fetch_open_interest'):
                    raise NotImplementedError(f"Exchange '{input_data.exchange}' does not support open interest")
                data = exchange_instance.fetch_open_interest(
                    symbol=input_data.symbol,
                    period=input_data.period,
                    limit=limit_val,
                    start_time=input_data.start_time,
                    end_time=input_data.end_time
                )
            
            return {
                "success": True,
                "data": {
                    "exchange": input_data.exchange,
                    "datatype": "open_interest",
                    "symbol": input_data.symbol,
                    "period": input_data.period,
                    "count": len(data),
                    "history": data
                }
            }
    except ValidationError as e:
        return {
            "success": False,
            "error_type": ErrorCode.VALIDATION_ERROR,
            "error_message": str(e),
            "meta": {"exchange": exchange, "symbol": symbol}
        }
    except ValueError as e:
        return {
            "success": False,
            "error_type": ErrorCode.INVALID_PARAMETER,
            "error_message": str(e),
            "meta": {"exchange": exchange, "symbol": symbol}
        }
    except httpx.HTTPError as e:
        return {
            "success": False,
            "error_type": ErrorCode.API_ERROR,
            "error_message": str(e),
            "meta": {"exchange": exchange, "symbol": symbol}
        }
    except NotImplementedError as e:
        return {
            "success": False,
            "error_type": ErrorCode.NOT_IMPLEMENTED,
            "error_message": str(e),
            "meta": {"exchange": exchange, "symbol": symbol}
        }
    except Exception as e:
        return {
            "success": False,
            "error_type": ErrorCode.UNKNOWN_ERROR,
            "error_message": str(e),
            "meta": {"exchange": exchange, "symbol": symbol}
        }

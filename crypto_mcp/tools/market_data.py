from typing import Literal, Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, ValidationError, field_validator
import httpx
from ..core.exchange_factory import ExchangeFactory
from ..core.errors import ErrorCode

class KlinesInput(BaseModel):
    exchange: Literal["binance", "bybit", "hyperliquid"] = Field(
        ...,
        description="The cryptocurrency exchange to fetch data from. Supported: 'binance', 'bybit', 'hyperliquid'."
    )
    symbol: str = Field(
        ...,
        description="The trading pair symbol (e.g., 'BTCUSDT')."
    )
    interval: str = Field(
        ...,
        description="The kline interval (e.g., '1h', '1d' for Binance; '60', 'D' for Bybit)."
    )
    market: Literal["spot", "futures"] = Field(
        "spot",
        description="The market type: 'spot' or 'futures'. Default is 'spot'."
    )
    start_time: Optional[int] = Field(
        None,
        description="Start time in milliseconds (inclusive)."
    )
    end_time: Optional[int] = Field(
        None,
        description="End time in milliseconds (inclusive)."
    )
    limit: int = Field(
        500,
        ge=1,
        le=1000,
        description="Number of klines to fetch. Default: 500. Max: 1000."
    )
    timezone: str = Field(
        "0",
        description="Timezone offset (e.g., '0' for UTC). Default is '0'."
    )

    @field_validator('symbol')
    @classmethod
    def sanitize_symbol(cls, v: str) -> str:
        return v.strip().upper()

    @field_validator('interval')
    @classmethod
    def sanitize_interval(cls, v: str) -> str:
        """Sanitize interval while preserving Bybit's numeric and uppercase formats."""
        v = v.strip()
        # Preserve Bybit's numeric intervals (e.g., '60', '120') and uppercase letters (D, W, M)
        # Convert lowercase D/W/M to uppercase for Bybit compatibility
        if v.isdigit():
            return v  # Preserve numeric strings for Bybit
        if v.upper() in ['D', 'W', 'M']:
            return v.upper()  # Convert D/W/M to uppercase for Bybit
        return v.lower()  # Lowercase string intervals for Binance

    @field_validator('start_time', 'end_time', mode='before')
    @classmethod
    def convert_timestamp(cls, v: Any) -> Optional[int]:
        """Convert string timestamps to integers."""
        if v is None:
            return None
        if isinstance(v, str):
            try:
                return int(v)
            except ValueError:
                return v
        return v

def get_klines(
    exchange: Literal["binance", "bybit", "hyperliquid"],
    symbol: str,
    interval: str,
    market: Literal["spot", "futures"] = "spot",
    start_time: Optional[Union[int, str]] = None,
    end_time: Optional[Union[int, str]] = None,
    limit: int = 500,
    timezone: str = "0",
    
    sessionId: Optional[str] = None,
    action: Optional[str] = None,
    chatInput: Optional[str] = None,
    toolCallId: Optional[str] = None
) -> dict:
    """
    Fetch OHLCV klines (candles).

    **Metric catalog**
    - Input-format notes: see `metrics://market_data`

    **Units**
    - `start_time` / `end_time` are **milliseconds**.

    **Intervals**
    - Binance: strings like `1h`, `4h`, `1d`
    - Bybit: numeric/letter like `60`, `240`, `D` (lowercase d/w/m are normalized)

    **Hyperliquid**
    - Historical klines are not supported here; use `get_hyperliquid_live_market_data`.

    Returns:
        { "success": true, "data": { "exchange": str, "symbol": str, "interval": str, "market": str, "count": int, "klines": [...] }, ... }
    """
    try:
        # Convert string timestamps to integers before validation
        if isinstance(start_time, str):
            try:
                start_time = int(start_time)
            except ValueError:
                pass
        if isinstance(end_time, str):
            try:
                end_time = int(end_time)
            except ValueError:
                pass

        # Validate inputs
        input_data = KlinesInput(
            exchange=exchange,
            symbol=symbol,
            interval=interval,
            market=market,
            start_time=start_time,
            end_time=end_time,
            limit=limit,
            timezone=timezone
        )

        # Use context manager for proper resource cleanup
        with ExchangeFactory.create(input_data.exchange) as exchange_instance:
            klines = exchange_instance.fetch_klines(
                symbol=input_data.symbol,
                interval=input_data.interval,
                limit=input_data.limit,
                start_time=input_data.start_time,
                end_time=input_data.end_time
            )

            return {
                "success": True,
                "data": {
                    "exchange": input_data.exchange,
                    "symbol": input_data.symbol,
                    "interval": input_data.interval,
                    "market": input_data.market,
                    "count": len(klines),
                    "klines": klines
                },
                "error_type": None,
                "error_message": None
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

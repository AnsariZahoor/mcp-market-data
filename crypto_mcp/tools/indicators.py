from typing import Literal, Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, ValidationError, field_validator
from ..core.exchange_factory import ExchangeFactory
from ..utils.indicators import TechnicalIndicators

class CalculateIndicatorInput(BaseModel):
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
        description="Kline interval (e.g., '1h', '1d' for Binance; '60', 'D' for Bybit)."
    )
    indicator: Literal[
        "RSI", "MACD", "SMA", "EMA", "BB", "ATR",
        "STOCH", "CCI", "OBV", "VWAP", "MFI", "KC"
    ] = Field(
        ...,
        description="Indicator name. Supported: RSI, MACD, SMA, EMA, BB, ATR, STOCH, CCI, OBV, VWAP, MFI, KC."
    )
    market: Literal["spot", "futures"] = Field(
        "spot",
        description="The trading market type. Defaults to 'spot'."
    )
    period: Optional[Union[int, str]] = Field(
        None,
        description="Period for calculation (optional, uses defaults if not provided). Accepts integer or string."
    )
    limit: int = Field(
        100,
        description="Number of klines to fetch. Defaults to 100."
    )

    @field_validator('period', mode='before')
    @classmethod
    def convert_period_to_int(cls, v: Any) -> Optional[int]:
        if v is None:
            return None
        if isinstance(v, str):
            try:
                return int(v)
            except ValueError:
                raise ValueError("Period must be a valid integer string or integer")
        if isinstance(v, int):
            return v
        raise ValueError("Period must be an integer or a string representation of an integer")

def calculate_indicator(
    exchange: Literal["binance", "bybit", "hyperliquid"],
    symbol: str,
    interval: str,
    indicator: Literal[
        "RSI", "MACD", "SMA", "EMA", "BB", "ATR",
        "STOCH", "CCI", "OBV", "VWAP", "MFI", "KC"
    ],
    market: Literal["spot", "futures"] = "spot",
    period: Optional[Union[int, str]] = None,
    limit: int = 100,
    
    sessionId: Optional[str] = None,
    action: Optional[str] = None,
    chatInput: Optional[str] = None,
    toolCallId: Optional[str] = None
) -> dict:
    """
    Calculate a technical indicator from historical klines.

    **Metric catalog**
    - Input-format notes: see `metrics://market_data`

    **Core constraints**
    - Requires historical candles from the selected exchange.
      - Binance/Bybit: OK
      - Hyperliquid: may fail if historical klines are not supported/available

    **Intervals**
    - Binance: strings like `1h`, `4h`, `1d`
    - Bybit: numeric/letter like `60`, `240`, `D`

    **Period defaults** (when `period` is omitted)
    - RSI: 14
    - SMA/EMA/BB/KC: 20
    - ATR/MFI: 14
    - CCI: 20
    - MACD/STOCH/OBV/VWAP: no period parameter

    **Limit guidance**
    - `limit` controls how many klines are fetched (more history).
    - For period-based indicators, prefer `limit >= period`.

    Returns:
        {
          "success": bool,
          "data": { "indicator": str, "data": [...] },
          "meta": { "exchange": str, "symbol": str, "interval": str, "market": str, "indicator": str, "period": int|None, "klines_count": int }
        }

    Examples:
        calculate_indicator(exchange="binance", symbol="BTCUSDT", interval="1h", indicator="RSI")
        calculate_indicator(exchange="bybit", symbol="BTCUSDT", interval="D", indicator="SMA", period=50)
    """
    try:
        # Convert string period to int if provided (MCP interface may pass strings)
        if period is not None and isinstance(period, str):
            try:
                period = int(period)
            except ValueError:
                raise ValueError("Period must be a valid integer string or integer")
        
        # Validate inputs
        input_data = CalculateIndicatorInput(
            exchange=exchange,
            symbol=symbol,
            interval=interval,
            indicator=indicator,
            market=market,
            period=period,
            limit=limit
        )

        # Fetch klines data
        with ExchangeFactory.create(input_data.exchange) as exchange_instance:
            klines = exchange_instance.fetch_klines(
                symbol=input_data.symbol,
                interval=input_data.interval,
                market=input_data.market,
                limit=input_data.limit
            )

        # Calculate indicator based on type
        ind = input_data.indicator
        p = input_data.period
        
        if ind == "RSI":
            result = TechnicalIndicators.calculate_rsi(klines, period=p or 14)
        elif ind == "MACD":
            result = TechnicalIndicators.calculate_macd(klines)
        elif ind == "SMA":
            result = TechnicalIndicators.calculate_sma(klines, period=p or 20)
        elif ind == "EMA":
            result = TechnicalIndicators.calculate_ema(klines, period=p or 20)
        elif ind == "BB":
            result = TechnicalIndicators.calculate_bollinger_bands(klines, period=p or 20)
        elif ind == "ATR":
            result = TechnicalIndicators.calculate_atr(klines, period=p or 14)
        elif ind == "STOCH":
            result = TechnicalIndicators.calculate_stochastic(klines)
        elif ind == "CCI":
            result = TechnicalIndicators.calculate_cci(klines, period=p or 20)
        elif ind == "OBV":
            result = TechnicalIndicators.calculate_obv(klines)
        elif ind == "VWAP":
            result = TechnicalIndicators.calculate_vwap(klines)
        elif ind == "MFI":
            result = TechnicalIndicators.calculate_mfi(klines, period=p or 14)
        elif ind == "KC":
            result = TechnicalIndicators.calculate_keltner_channels(klines, period=p or 20)
        else:
            # Should be caught by Pydantic, but just in case
            raise ValueError(f"Unknown indicator: {ind}")

        return {
            "success": True,
            "data": result,
            "error_type": None,
            "error_message": None,
            "meta": {
                "exchange": input_data.exchange,
                "symbol": input_data.symbol,
                "interval": input_data.interval,
                "market": input_data.market,
                "indicator": input_data.indicator,
                "period": input_data.period,
                "klines_count": len(klines)
            }
        }

    except ValidationError as e:
        return {
            "success": False,
            "data": None,
            "error_type": "ValidationError",
            "error_message": str(e),
            "meta": {
                "exchange": exchange,
                "symbol": symbol,
                "indicator": indicator
            }
        }
    except ValueError as e:
        return {
            "success": False,
            "data": None,
            "error_type": "ValueError",
            "error_message": str(e),
            "meta": {
                "exchange": exchange,
                "symbol": symbol,
                "indicator": indicator
            }
        }
    except Exception as e:
        return {
            "success": False,
            "data": None,
            "error_type": type(e).__name__,
            "error_message": str(e),
            "meta": {
                "exchange": exchange,
                "symbol": symbol,
                "indicator": indicator
            }
        }

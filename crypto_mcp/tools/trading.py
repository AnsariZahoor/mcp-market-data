from typing import Literal, Optional
from pydantic import BaseModel, Field, ValidationError
import httpx
from ..core.exchange_factory import ExchangeFactory

class TradingPairsInput(BaseModel):
    exchange: Literal["binance", "bybit", "hyperliquid"] = Field(
        ...,
        description="The cryptocurrency exchange to fetch data from. Supported: 'binance', 'bybit', 'hyperliquid'."
    )
    market: Literal["spot", "futures"] = Field(
        ...,
        description="The trading market type. Supported: 'spot', 'futures'."
    )
    status: Literal["active", "inactive", "all"] = Field(
        "active",
        description="Filter pairs by trading status. 'active' for currently trading, 'inactive' for delisted/paused, 'all' for both."
    )

def get_trading_pairs(
    exchange: str,
    market: Literal["spot", "futures"],
    status: Literal["active", "inactive", "all"] = "active",
    
    sessionId: Optional[str] = None,
    action: Optional[str] = None,
    chatInput: Optional[str] = None,
    toolCallId: Optional[str] = None
) -> dict:
    """
    Fetch trading pairs for an exchange + market (discovery tool).

    Prefer using resources for discovery when possible:
    - `exchange://list`
    - `exchange://{exchange}/{market}/active` / `exchange://{exchange}/{market}/inactive`

    Args:
        exchange: `binance` | `bybit` | `hyperliquid`
        market: `spot` | `futures`
        status: `active` | `inactive` | `all`

    Returns:
        { "success": true, "data": { "exchange": str, "market": str, "count": int, "pairs": [...] }, ... }

    Example:
        get_trading_pairs(exchange="binance", market="spot", status="active")
    """
    try:
        # Validate inputs using Pydantic model
        input_data = TradingPairsInput(exchange=exchange, market=market, status=status)
        
        # Use context manager for proper resource cleanup
        with ExchangeFactory.create(input_data.exchange) as exchange_instance:
            # Fetch all pairs for the market
            result = exchange_instance.fetch_all_pairs(input_data.market)

            # Filter based on status
            if input_data.status == "active":
                pairs = result["active"]
            elif input_data.status == "inactive":
                pairs = result["inactive"]
            else:  # all
                pairs = result["active"] + result["inactive"]

            return {
                "success": True,
                "data": {
                    "exchange": input_data.exchange,
                    "market": input_data.market,
                    "count": len(pairs),
                    "pairs": pairs
                },
                "error_type": None,
                "error_message": None,
                "meta": {
                    "status_filter": input_data.status,
                    "timestamp": "latest" # In a real app, use actual timestamp
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
                "market": market,
                "status": status
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
                "market": market
            }
        }
    except httpx.HTTPError as e:
        return {
            "success": False,
            "data": None,
            "error_type": "HTTPError",
            "error_message": str(e),
            "meta": {
                "exchange": exchange,
                "market": market
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
                "market": market
            }
        }


def list_supported_exchanges(
    sessionId: Optional[str] = None,
    action: Optional[str] = None,
    chatInput: Optional[str] = None,
    toolCallId: Optional[str] = None
) -> dict:
    """
    List supported exchanges and their supported markets (discovery tool).

    Returns:
        { "success": true, "data": { "count": int, "exchanges": [...] }, ... }

    Example:
        list_supported_exchanges()
    """
    try:
        exchanges = ExchangeFactory.list_exchanges()
        exchange_info = []

        for exchange_name in exchanges:
            info = ExchangeFactory.get_exchange_info(exchange_name)
            exchange_info.append({
                "name": info["name"],
                "markets": info["supported_markets"],
                "description": info["description"].strip()
            })

        return {
            "success": True,
            "data": {
                "count": len(exchanges),
                "exchanges": exchange_info
            },
            "error_type": None,
            "error_message": None,
            "meta": {
                "timestamp": "latest"
            }
        }
    except Exception as e:
        return {
            "success": False,
            "data": None,
            "error_type": type(e).__name__,
            "error_message": str(e),
            "meta": {}
        }

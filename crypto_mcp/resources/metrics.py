import json
from fastmcp import FastMCP


def register_metrics_resources(mcp: FastMCP) -> None:
    """
    Register metric-catalog resources (exchange data only, no proprietary metrics).
    """

    @mcp.resource("metrics://index")
    def metrics_index() -> str:
        return json.dumps(
            {
                "success": True,
                "data": {
                    "catalogs": [
                        {
                            "uri": "metrics://market_data",
                            "description": "Klines + derivatives quick reference (ms timestamps, interval formats).",
                        },
                    ],
                    "notes": [
                        "Timestamp units are milliseconds for klines, funding rate, and open interest.",
                        "Use exchange resources (`exchange://...`) to discover valid symbols first.",
                    ],
                },
                "error_type": None,
                "error_message": None,
            },
            indent=2,
        )

    @mcp.resource("metrics://market_data")
    def metrics_market_data() -> str:
        return json.dumps(
            {
                "success": True,
                "data": {
                    "notes": [
                        "This catalog is for input-format sanity (not a metric list).",
                        "Use exchange resources (`exchange://...`) to discover valid symbols first.",
                    ],
                    "tools": ["get_klines", "get_funding_rate", "get_open_interest", "calculate_indicator", "get_hyperliquid_live_market_data"],
                    "units": {
                        "get_klines.start_time": "milliseconds",
                        "get_klines.end_time": "milliseconds",
                        "get_funding_rate.start_time": "milliseconds",
                        "get_funding_rate.end_time": "milliseconds",
                        "get_open_interest.start_time": "milliseconds",
                        "get_open_interest.end_time": "milliseconds",
                    },
                    "intervals": {
                        "binance": ["1m", "5m", "15m", "30m", "1h", "4h", "1d", "1w", "1M"],
                        "bybit": ["1", "3", "5", "15", "30", "60", "120", "240", "360", "720", "D", "W", "M"],
                    },
                    "hyperliquid": {"historical_klines": False, "live_snapshot_tool": "get_hyperliquid_live_market_data"},
                },
                "error_type": None,
                "error_message": None,
            },
            indent=2,
        )

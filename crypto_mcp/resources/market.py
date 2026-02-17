import json
from fastmcp import FastMCP
from ..tools.trading import get_trading_pairs, list_supported_exchanges

def register_market_resources(mcp: FastMCP):
    """Register market-related resources with the MCP server."""

    @mcp.resource("exchange://list")
    def get_exchanges_resource() -> str:
        """
        MCP Resource: List of all supported exchanges
        
        Returns:
            JSON string with exchange information
        """
        result = list_supported_exchanges()
        return json.dumps(result, indent=2)

    @mcp.resource("exchange://{exchange}/{market}/active")
    def get_active_pairs_resource(exchange: str, market: str) -> str:
        """
        MCP Resource: Active trading pairs for a specific exchange and market
        
        Args:
            exchange: Exchange name
            market: Market type
            
        Returns:
            JSON string with active trading pairs
        """
        # Resources use tools which already handle context management
        result = get_trading_pairs(exchange, market, "active")
        return json.dumps(result, indent=2)

    @mcp.resource("exchange://{exchange}/{market}/inactive")
    def get_inactive_pairs_resource(exchange: str, market: str) -> str:
        """
        MCP Resource: Inactive trading pairs for a specific exchange and market
        
        Args:
            exchange: Exchange name
            market: Market type
            
        Returns:
            JSON string with inactive trading pairs
        """
        # Resources use tools which already handle context management
        result = get_trading_pairs(exchange, market, "inactive")
        return json.dumps(result, indent=2)

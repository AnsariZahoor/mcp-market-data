from fastmcp import Client
import asyncio
import os

from dotenv import load_dotenv

load_dotenv()

MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8000/mcp")

async def discord_auth():
    """Test Discord OAuth authentication."""
    async with Client(MCP_SERVER_URL, auth="oauth") as client:
        print("✓ Authenticated with Discord!")
        result = await client.call_tool("get_user_info")
        print(f"Discord user: {result.data['username']}")

async def api_key_auth():
    """Test API key authentication."""
    api_key = os.getenv("CRYPTO_MCP_API_KEY")
    if not api_key:
        print("✗ Set CRYPTO_MCP_API_KEY env var first")
        return
    
    print(f"Using API key: {api_key[:20]}...")
    
    # Method 1: Pass as bearer token string
    async with Client(MCP_SERVER_URL, auth=f"Bearer {api_key}") as client:
        print("✓ Authenticated with API key!")
        result = await client.call_tool("list_supported_exchanges")
        print(f"Exchanges: {result.data}")


async def privy_auth():
    """Test Privy OAuth authentication."""
    async with Client(MCP_SERVER_URL, auth="oauth") as client:
        print("✓ Authenticated with Privy!")
        result = await client.call_tool("get_user_info")
        print(result)

async def auth0_auth():
    # The client will automatically handle Auth0 OAuth flows
    async with Client("http://localhost:8000/mcp", auth="oauth") as client:
        # First-time connection will open Auth0 login in your browser
        print("✓ Authenticated with Auth0!")

        # Test the protected tool
        result = await client.call_tool("get_token_info")
        print(f"Auth0 audience: {result['audience']}")

if __name__ == "__main__":
    # asyncio.run(api_key_auth())
    asyncio.run(privy_auth())
    # asyncio.run(auth0_auth())
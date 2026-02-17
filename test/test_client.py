from fastmcp import Client
import asyncio
import os

from dotenv import load_dotenv

load_dotenv()

MCP_SERVER_URL = os.getenv("MCP_SERVER_URL")
if not MCP_SERVER_URL:
    print("✗ Set MCP_SERVER_URL env var first")
    exit(1)

async def discord_auth():
    """Test Discord OAuth authentication."""
    async with Client(MCP_SERVER_URL, auth="oauth") as client:
        print("✓ Authenticated with Discord!")
        result = await client.call_tool("get_user_info")
        print(f"Discord user: {result.data['username']}")

async def api_key_auth():
    """Test API key authentication."""
    api_key = os.getenv("PANDA_MCP_API_KEY")
    if not api_key:
        print("✗ Set PANDA_MCP_API_KEY env var first")
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


if __name__ == "__main__":
    # asyncio.run(api_key_auth())
    asyncio.run(privy_auth())
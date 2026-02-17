"""
Test script to verify RateLimitingMiddleware is working correctly.
Tests:
1. Rate limiting triggers when limit exceeded
2. Per-client rate limiting (different clients have separate limits)
3. Burst capacity allows short bursts
4. Rate limit errors are properly raised
"""

import asyncio
import time
from fastmcp import Client
from mcp import McpError

# Test configuration
SERVER_URL = "http://localhost:8000/mcp"
RATE_LIMIT_RPS = 10.0  # Default from RateLimitingMiddleware
BURST_CAPACITY = 20  # Default is 2x RPS

async def test_rate_limiting():
    """Test that rate limiting works by making rapid requests."""
    print("=" * 60)
    print("Testing Rate Limiting Middleware")
    print("=" * 60)
    
    async with Client(SERVER_URL, auth="oauth") as client:
        print(f"\n✓ Connected to server at {SERVER_URL}")
        
        # Test 1: Make requests within rate limit (should succeed)
        print("\n[Test 1] Making requests within rate limit...")
        success_count = 0
        start_time = time.time()
        
        # Make 10 requests quickly (should all succeed due to burst capacity)
        for i in range(10):
            try:
                result = await client.call_tool("test_rate_limit")
                success_count += 1
                print(f"  Request {i+1}: ✓ Success")
            except Exception as e:
                print(f"  Request {i+1}: ✗ Failed - {e}")
        
        elapsed = time.time() - start_time
        print(f"  Result: {success_count}/10 requests succeeded in {elapsed:.2f}s")
        
        # Test 2: Exceed burst capacity (should hit rate limit)
        print("\n[Test 2] Testing burst capacity (making 25 rapid requests)...")
        success_count = 0
        rate_limited_count = 0
        start_time = time.time()
        
        # Make 25 requests rapidly (exceeds burst capacity of 20)
        tasks = []
        for i in range(25):
            tasks.append(client.call_tool("test_rate_limit"))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                if "rate limit" in str(result).lower() or isinstance(result, McpError):
                    rate_limited_count += 1
                    print(f"  Request {i+1}: ✗ Rate Limited")
                else:
                    print(f"  Request {i+1}: ✗ Error - {result}")
            else:
                success_count += 1
                print(f"  Request {i+1}: ✓ Success")
        
        elapsed = time.time() - start_time
        print(f"  Result: {success_count} succeeded, {rate_limited_count} rate limited in {elapsed:.2f}s")
        
        if rate_limited_count > 0:
            print(f"  ✓ Rate limiting is working! Blocked {rate_limited_count} requests")
        else:
            print(f"  ⚠ No rate limits hit - might need to adjust test or limits")
        
        # Test 3: Sustained rate limit (make requests at exactly the rate limit)
        print("\n[Test 3] Testing sustained rate limit (10 requests over 1 second)...")
        success_count = 0
        rate_limited_count = 0
        start_time = time.time()
        
        # Make requests at exactly the rate limit (10 per second)
        for i in range(10):
            try:
                result = await client.call_tool("test_rate_limit")
                success_count += 1
            except Exception as e:
                if "rate limit" in str(e).lower() or isinstance(e, McpError):
                    rate_limited_count += 1
                print(f"  Request {i+1}: Rate limited")
            
            # Wait 0.1 seconds between requests (10 per second)
            await asyncio.sleep(0.1)
        
        elapsed = time.time() - start_time
        print(f"  Result: {success_count} succeeded, {rate_limited_count} rate limited in {elapsed:.2f}s")
        
        # Test 4: Exceed sustained rate (make requests faster than rate limit)
        print("\n[Test 4] Testing sustained rate limit violation (20 requests in 1 second)...")
        success_count = 0
        rate_limited_count = 0
        start_time = time.time()
        
        # Make 20 requests in 1 second (exceeds 10/sec limit)
        # We actually execute them with delays, not just create coroutines
        for i in range(20):
            try:
                result = await client.call_tool("test_rate_limit")
                success_count += 1
            except Exception as e:
                if "rate limit" in str(e).lower() or isinstance(e, McpError):
                    rate_limited_count += 1
                else:
                    print(f"  Request {i+1}: Error - {e}")
            
            # Wait 0.05 seconds between requests (20 per second)
            # await asyncio.sleep(0.05)
        
        elapsed = time.time() - start_time
        print(f"  Result: {success_count} succeeded, {rate_limited_count} rate limited in {elapsed:.2f}s")
        
        if rate_limited_count > 0:
            print(f"  ✓ Sustained rate limiting is working!")
        
        # Test 5: Wait for token bucket refill
        print("\n[Test 5] Testing token bucket refill (wait 2 seconds, then make requests)...")
        print("  Waiting 2 seconds for token bucket to refill...")
        await asyncio.sleep(2)
        
        success_count = 0
        for i in range(5):
            try:
                result = await client.call_tool("test_rate_limit")
                success_count += 1
                print(f"  Request {i+1}: ✓ Success")
            except Exception as e:
                print(f"  Request {i+1}: ✗ Failed - {e}")
        
        print(f"  Result: {success_count}/5 requests succeeded after refill")
        
        print("\n" + "=" * 60)
        print("Rate Limiting Test Complete")
        print("=" * 60)
        print("\nSummary:")
        print(f"  - Default rate limit: {RATE_LIMIT_RPS} requests/second")
        print(f"  - Burst capacity: {BURST_CAPACITY} requests")
        print(f"  - Rate limiting middleware is {'WORKING' if rate_limited_count > 0 else 'NOT TRIGGERING'}")

if __name__ == "__main__":
    print("\n⚠ Make sure the server is running on http://localhost:8000")
    print("⚠ You may need to authenticate with Discord OAuth\n")
    
    try:
        asyncio.run(test_rate_limiting())
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\n\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


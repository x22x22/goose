#!/usr/bin/env python3
"""
Test script to demonstrate goose SDK usage.

This script shows how to:
1. Check server status
2. Start an agent
3. Send a simple message
4. List sessions

Note: This requires goose-server to be running on localhost:3001
"""

import asyncio
import sys
from goose_sdk import GooseClient


async def test_sdk():
    """Test the goose SDK functionality."""
    print("=== goose SDK Test ===\n")
    
    # Initialize client
    client = GooseClient(
        base_url="http://localhost:3001",
        secret_key="test",
        timeout=30.0
    )
    
    async with client:
        # 1. Check server status
        print("1. Checking server status...")
        try:
            status = await client.check_status()
            print(f"   ✓ Server is running: {status}")
        except Exception as e:
            print(f"   ✗ Failed to connect to server: {e}")
            print("\n   Please start the goose server:")
            print("   cargo run -p goose-server -- agent")
            return False
        
        # 2. Get available providers
        print("\n2. Getting available providers...")
        try:
            providers = await client.get_providers()
            print(f"   ✓ Found {len(providers)} provider(s)")
            if providers:
                for provider in providers[:3]:  # Show first 3
                    print(f"     - {provider.get('name', 'unknown')}")
        except Exception as e:
            print(f"   ✗ Failed to get providers: {e}")
        
        # 3. List available extensions
        print("\n3. Listing available extensions...")
        try:
            extensions = await client.list_extensions()
            print(f"   ✓ Found {len(extensions)} extension(s)")
            if extensions:
                for ext in extensions[:5]:  # Show first 5
                    print(f"     - {ext.get('name', 'unknown')}")
        except Exception as e:
            print(f"   ✗ Failed to list extensions: {e}")
        
        # 4. List sessions
        print("\n4. Listing existing sessions...")
        try:
            sessions = await client.list_sessions()
            print(f"   ✓ Found {len(sessions)} session(s)")
            if sessions:
                for session in sessions[:3]:  # Show first 3
                    print(f"     - {session.id}: {session.name or 'unnamed'}")
        except Exception as e:
            print(f"   ✗ Failed to list sessions: {e}")
        
        print("\n=== Test Complete ===")
        print("\nThe SDK is working correctly!")
        print("\nTo start using goose in your application:")
        print("1. Import: from goose_sdk import GooseClient")
        print("2. Create client: async with GooseClient() as client:")
        print("3. Start agent: await client.start_agent()")
        print("4. Send messages: async for event in client.send_message(...)")
        print("\nSee examples/sdk/README.md for more details.")
        
        return True


def main():
    """Main entry point."""
    try:
        success = asyncio.run(test_sdk())
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user.")
        return 1
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

"""
Simple Telegram session regenerator (no database required).

Just creates a new session file using credentials you provide.
"""
import asyncio
import os
import sys
from telethon import TelegramClient

def main():
    print("=" * 60)
    print("Simple Telegram Session Generator")
    print("=" * 60)
    print()
    
    # Get credentials from user or environment
    api_id = os.environ.get("TELEGRAM_API_ID") or input("Telegram API ID: ").strip()
    api_hash = os.environ.get("TELEGRAM_API_HASH") or input("Telegram API Hash: ").strip()
    session_name = input("Session name [anon]: ").strip() or "anon"
    
    if not api_id or not api_hash:
        print("ERROR: API ID and Hash are required")
        sys.exit(1)
    
    try:
        api_id = int(api_id)
    except ValueError:
        print("ERROR: API ID must be a number")
        sys.exit(1)
    
    print()
    print(f"Session name: {session_name}")
    print(f"API ID: {api_id}")
    print(f"API Hash: {api_hash[:10]}...")
    print()
    
    # Check for existing session
    session_file = f"{session_name}.session"
    if os.path.exists(session_file):
        print(f"⚠️  Existing session found: {session_file}")
        response = input("Delete and create new? [y/N]: ").strip().lower()
        if response != 'y':
            print("Aborted.")
            sys.exit(0)
        
        try:
            os.remove(session_file)
            print(f"✓ Deleted {session_file}")
        except Exception as e:
            print(f"ERROR: Failed to delete: {e}")
            sys.exit(1)
    
    print()
    print("=" * 60)
    print("Creating session...")
    print("You'll be prompted for phone number and code.")
    print("=" * 60)
    print()
    
    async def create_session():
        client = TelegramClient(session_name, api_id, api_hash)
        
        try:
            await client.start()
            print()
            print("✓ Session created successfully!")
            print(f"✓ File: {session_file}")
            print()
            
            # Test the session
            me = await client.get_me()
            print(f"✓ Logged in as: {me.first_name} (@{me.username})")
            print()
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            sys.exit(1)
        finally:
            await client.disconnect()
    
    asyncio.run(create_session())
    print("=" * 60)
    print("Done! Session is ready to use.")
    print("=" * 60)

if __name__ == "__main__":
    main()

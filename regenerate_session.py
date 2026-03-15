"""
Regenerate Telegram session after AuthKeyDuplicatedError.

This script:
1. Deletes the old session file
2. Starts an interactive login to create a new session
3. Saves the new session for the bot to use

IMPORTANT: Run this ONLY on the server (DigitalOcean) where the bot will run.
Do NOT run it locally if the bot runs remotely.
"""
import os
import sys
import asyncio
from telethon import TelegramClient

# Ensure db module is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import db

def main():
    print("=" * 60)
    print("Telegram Session Regeneration")
    print("=" * 60)
    print()
    
    # Load settings from DB
    if not os.environ.get("BACKUP_DB_ADMIN_URL"):
        print("ERROR: BACKUP_DB_ADMIN_URL environment variable is not set.")
        sys.exit(1)
    
    db.init_db()
    settings = db.get_all_settings()
    
    api_id_str = settings.get("telegram_api_id")
    api_hash = settings.get("telegram_api_hash")
    session_name = settings.get("telegram_session_name", "anon")
    
    if not api_id_str or not api_hash:
        print("ERROR: telegram_api_id and telegram_api_hash must be set in DB.")
        sys.exit(1)
    
    api_id = int(api_id_str)
    
    print(f"Session name: {session_name}")
    print(f"API ID: {api_id}")
    print(f"API Hash: {api_hash[:10]}...")
    print()
    
    # Check for existing session file
    session_file = f"{session_name}.session"
    if os.path.exists(session_file):
        print(f"⚠️  Found existing session file: {session_file}")
        response = input("Delete it and create a new one? [y/N]: ").strip().lower()
        if response != 'y':
            print("Aborted.")
            sys.exit(0)
        
        try:
            os.remove(session_file)
            print(f"✓ Deleted {session_file}")
        except Exception as e:
            print(f"ERROR: Failed to delete session file: {e}")
            sys.exit(1)
    else:
        print(f"No existing session file found ({session_file})")
    
    print()
    print("=" * 60)
    print("Creating new Telegram session...")
    print("You will be prompted for your phone number and code.")
    print("=" * 60)
    print()
    
    async def create_session():
        client = TelegramClient(session_name, api_id, api_hash)
        await client.start()
        print()
        print("✓ Session created successfully!")
        print(f"✓ Session file saved as: {session_file}")
        print()
        print("You can now run the bot normally.")
        await client.disconnect()
    
    asyncio.run(create_session())

if __name__ == "__main__":
    main()

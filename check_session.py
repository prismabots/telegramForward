#!/usr/bin/env python3
"""
Auto-regenerate Telegram session on startup if it's invalid.

This script checks if the session is valid and regenerates it if needed.
Useful for DigitalOcean App Platform where manual intervention is difficult.
"""
import os
import sys
import asyncio
from telethon import TelegramClient
from telethon.errors import AuthKeyDuplicatedError

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import db

async def check_and_regenerate_session():
    """Check if session is valid, regenerate if not."""
    print("Checking Telegram session validity...")
    
    # Load settings
    if not os.environ.get("BACKUP_DB_ADMIN_URL"):
        print("ERROR: BACKUP_DB_ADMIN_URL not set")
        return False
    
    db.init_db()
    settings = db.get_all_settings()
    
    api_id = int(settings.get("telegram_api_id"))
    api_hash = settings.get("telegram_api_hash")
    session_name = settings.get("telegram_session_name", "anon")
    
    # Auto-regenerate using phone number from environment
    phone = os.environ.get("TELEGRAM_PHONE")
    if not phone:
        print("ERROR: TELEGRAM_PHONE environment variable not set")
        print("Set it in DigitalOcean App Platform settings")
        return False
    
    client = TelegramClient(session_name, api_id, api_hash)
    
    try:
        # Try to connect with existing session
        await client.connect()
        
        if not await client.is_user_authorized():
            print("Session not authorized, requesting code...")
            await client.send_code_request(phone)
            print(f"⚠️  Verification code sent to {phone}")
            print("⚠️  You need to set TELEGRAM_CODE in environment and redeploy")
            await client.disconnect()
            return False
        
        print("✓ Session is valid!")
        await client.disconnect()
        return True
        
    except AuthKeyDuplicatedError:
        print("⚠️  AuthKeyDuplicatedError detected - session is invalid")
        print("Attempting to regenerate...")
        
        # Close and delete old session
        try:
            await client.disconnect()
        except:
            pass
        
        session_file = f"{session_name}.session"
        if os.path.exists(session_file):
            os.remove(session_file)
            print(f"Deleted old session file: {session_file}")
        
        # Create new session (requires manual code entry)
        print(f"⚠️  Manual intervention required:")
        print(f"⚠️  Run: python regenerate_session.py")
        print(f"⚠️  Or set TELEGRAM_CODE in environment and redeploy")
        
        return False
        
    except Exception as e:
        print(f"Error checking session: {e}")
        await client.disconnect()
        return False

if __name__ == "__main__":
    result = asyncio.run(check_and_regenerate_session())
    sys.exit(0 if result else 1)

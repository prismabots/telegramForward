#!/usr/bin/env python3
"""
Session initializer for DigitalOcean App Platform.

This script runs BEFORE main.py and creates the session if it doesn't exist
or is invalid. It uses environment variables for authentication.

Required environment variables:
- TELEGRAM_PHONE: Phone number (e.g., +1234567890)
- TELEGRAM_CODE: Verification code (optional, for initial setup)
- TELEGRAM_PASSWORD: 2FA password (optional, if 2FA is enabled)
"""
import os
import sys
import asyncio
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError, AuthKeyDuplicatedError

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import db

async def init_session():
    """Initialize or validate Telegram session."""
    print("=" * 70)
    print("Telegram Session Initializer")
    print("=" * 70)
    
    # Load settings
    db_url = os.environ.get("BACKUP_DB_ADMIN_URL")
    if not db_url:
        print("❌ BACKUP_DB_ADMIN_URL not set")
        return False
    
    db.init_db()
    settings = db.get_all_settings()
    
    api_id = int(settings.get("telegram_api_id"))
    api_hash = settings.get("telegram_api_hash")
    session_name = settings.get("telegram_session_name", "anon")
    
    phone = os.environ.get("TELEGRAM_PHONE")
    code = os.environ.get("TELEGRAM_CODE")
    password = os.environ.get("TELEGRAM_PASSWORD")
    
    session_file = f"{session_name}.session"
    
    print(f"Session file: {session_file}")
    print(f"Phone: {phone if phone else 'Not set'}")
    print(f"API ID: {api_id}")
    print()
    
    client = TelegramClient(session_name, api_id, api_hash)
    
    try:
        await client.connect()
        
        # Check if already authorized
        if await client.is_user_authorized():
            print("✓ Session is valid and authorized")
            me = await client.get_me()
            print(f"✓ Logged in as: {me.first_name} (@{me.username})")
            await client.disconnect()
            return True
        
        # Need to authorize
        if not phone:
            print("❌ TELEGRAM_PHONE environment variable required for first-time setup")
            await client.disconnect()
            return False
        
        print(f"Sending code request to {phone}...")
        await client.send_code_request(phone)
        
        if not code:
            print("❌ TELEGRAM_CODE environment variable required")
            print("Check your Telegram app for the code and set it in App Platform")
            await client.disconnect()
            return False
        
        print(f"Signing in with code...")
        try:
            await client.sign_in(phone, code)
        except SessionPasswordNeededError:
            if not password:
                print("❌ 2FA enabled - TELEGRAM_PASSWORD environment variable required")
                await client.disconnect()
                return False
            print("Signing in with 2FA password...")
            await client.sign_in(password=password)
        
        me = await client.get_me()
        print(f"✓ Successfully signed in as: {me.first_name} (@{me.username})")
        await client.disconnect()
        return True
        
    except AuthKeyDuplicatedError:
        print("⚠️  AuthKeyDuplicatedError - deleting old session...")
        try:
            await client.disconnect()
        except:
            pass
        
        if os.path.exists(session_file):
            os.remove(session_file)
            print(f"✓ Deleted {session_file}")
        
        # Retry with fresh session
        print("Retrying with fresh session...")
        return await init_session()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        await client.disconnect()
        return False

if __name__ == "__main__":
    print()
    result = asyncio.run(init_session())
    print()
    
    if result:
        print("=" * 70)
        print("✓ Session ready - starting bot...")
        print("=" * 70)
        sys.exit(0)
    else:
        print("=" * 70)
        print("❌ Session initialization failed")
        print("=" * 70)
        sys.exit(1)

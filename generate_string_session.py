#!/usr/bin/env python3
"""
Generate a Telegram string session that can be used as an environment variable.

This is the BEST solution for DigitalOcean App Platform because:
1. String sessions don't get invalidated by IP changes as easily
2. Can be stored as environment variable (no files needed)
3. One-time setup, works forever
"""
import asyncio
import sys
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import SessionPasswordNeededError

async def generate_string_session():
    print("=" * 70)
    print("Telegram String Session Generator")
    print("=" * 70)
    print()
    print("This will generate a session string that you can store as an")
    print("environment variable in DigitalOcean App Platform.")
    print()
    
    # Get credentials
    api_id = input("Telegram API ID: ").strip()
    api_hash = input("Telegram API Hash: ").strip()
    phone = input("Phone number (with country code, e.g., +1234567890): ").strip()
    
    try:
        api_id = int(api_id)
    except ValueError:
        print("❌ API ID must be a number")
        return None
    
    print()
    print("Creating session...")
    print()
    
    # Create client with StringSession
    client = TelegramClient(StringSession(), api_id, api_hash)
    
    try:
        await client.connect()
        
        # Send code request
        print(f"Sending verification code to {phone}...")
        await client.send_code_request(phone)
        
        # Get code from user
        code = input("Enter the verification code from Telegram: ").strip()
        
        try:
            # Try to sign in
            await client.sign_in(phone, code)
        except SessionPasswordNeededError:
            # 2FA is enabled
            print()
            print("⚠️  2FA (Two-Factor Authentication) is enabled on your account")
            password = input("Enter your 2FA password: ").strip()
            await client.sign_in(password=password)
        
        # Get user info
        me = await client.get_me()
        print()
        print("=" * 70)
        print(f"✓ Successfully logged in as: {me.first_name} (@{me.username})")
        print("=" * 70)
        print()
        
        # Get the session string
        session_string = client.session.save()
        
        print("Your session string (SAVE THIS):")
        print()
        print("=" * 70)
        print(session_string)
        print("=" * 70)
        print()
        print("📋 INSTRUCTIONS:")
        print()
        print("1. Copy the session string above (the long text)")
        print()
        print("2. In DigitalOcean App Platform:")
        print("   - Go to Settings → Environment Variables")
        print("   - Add a new variable:")
        print()
        print("     TELEGRAM_SESSION_STRING = (paste the string here)")
        print()
        print("3. That's it! The bot will use this session automatically.")
        print()
        print("⚠️  IMPORTANT: Keep this string SECRET - it's like your password!")
        print()
        
        await client.disconnect()
        return session_string
        
    except Exception as e:
        print(f"❌ Error: {e}")
        await client.disconnect()
        return None

if __name__ == "__main__":
    session = asyncio.run(generate_string_session())
    sys.exit(0 if session else 1)

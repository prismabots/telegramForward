#!/usr/bin/env python3
"""Diagnose T2T Gold channel issues."""
import os
import sys

print("=" * 80)
print("T2T GOLD CHANNEL DIAGNOSTICS")
print("=" * 80)
print()

# Check 1: Environment variables
print("1. ENVIRONMENT VARIABLES:")
print(f"   BACKUP_DB_ADMIN_URL: {'✓ Set' if os.environ.get('BACKUP_DB_ADMIN_URL') else '✗ NOT SET'}")
print(f"   X_API_KEY (Grok): {'✓ Set' if os.environ.get('X_API_KEY') else '✗ NOT SET'}")
print(f"   GOOGLE_API_KEY (Gemini): {'✓ Set' if os.environ.get('GOOGLE_API_KEY') else '✗ NOT SET'}")
print(f"   TELEGRAM_STRING_SESSION: {'✓ Set' if os.environ.get('TELEGRAM_STRING_SESSION') else '✗ NOT SET'}")
print()

# Check 2: Database connection
print("2. DATABASE CONNECTION:")
try:
    import db
    channels = db.get_channels(enabled_only=False)
    print(f"   ✓ Connected, {len(channels)} channels loaded")
except Exception as e:
    print(f"   ✗ Error: {e}")
print()

# Check 3: T2T Channel details
print("3. T2T GOLD CHANNEL DETAILS:")
try:
    import db
    channels = db.get_channels(enabled_only=False)
    t2t = next((ch for ch in channels if 'T2T' in ch['name']), None)
    if t2t:
        print(f"   ID: {t2t['id']}")
        print(f"   Enabled: {t2t['enabled']}")
        print(f"   AI Enabled: {t2t['ai_enabled']}")
        print(f"   Chat ID: {t2t['chat_id']}")
        print(f"   Discord Webhook Valid: {t2t['discord_webhook'][:40]}...")
        print(f"   ✓ Channel found and configured")
    else:
        print(f"   ✗ Channel not found in database")
except Exception as e:
    print(f"   ✗ Error: {e}")
print()

# Check 4: API Keys (Grok specifically)
print("4. GROK API KEY STATUS:")
api_key = os.environ.get('X_API_KEY')
if api_key:
    print(f"   ✓ Key present ({len(api_key)} chars)")
    print(f"   ℹ️  Last 10 chars: ...{api_key[-10:]}")
    # Check if it looks valid (usually starts with xai- or similar)
    if api_key.lower().startswith(('xai-', 'sk-', 'glm-')):
        print(f"   ✓ Format looks valid")
    else:
        print(f"   ⚠ Format might be incorrect")
else:
    print(f"   ✗ NO GROK API KEY SET")
print()

# Check 5: Fallback configuration
print("5. FALLBACK CONFIGURATION:")
try:
    import db
    channels = db.get_channels(enabled_only=False)
    t2t = next((ch for ch in channels if 'T2T' in ch['name']), None)
    if t2t:
        print(f"   Primary: {t2t.get('ai_provider') or '(global)'} / {t2t.get('ai_model') or '(default)'}")
        print(f"   Fallback: {t2t.get('ai_fallback_provider')} / {t2t.get('ai_fallback_model')}")
        if t2t.get('ai_fallback_provider'):
            print(f"   ✓ Fallback configured")
        else:
            print(f"   ⚠ No fallback configured")
except Exception as e:
    print(f"   ✗ Error: {e}")
print()

# Check 6: Recent messages (if possible)
print("6. POSSIBLE ISSUES & SOLUTIONS:")
print()
print("   If T2T Gold has stopped receiving messages, check:")
print()
print("   A. Bot Status:")
print("      → Is main.py running on DigitalOcean App Platform?")
print("      → Check App Platform runtime logs")
print("      → Look for crashes or authentication errors")
print()
print("   B. Grok API:")
print("      → Is Grok API still working? (check X_API_KEY)")
print("      → Has the API quota been exceeded?")
print("      → Check Grok status page")
print()
print("   C. Discord Webhook:")
print("      → Test webhook manually")
print("      → Webhook format: https://discord.com/api/webhooks/ID/TOKEN")
print()
print("   D. Telegram Connection:")
print("      → Is Telegram connection still authenticated?")
print("      → Check for session expiration")
print()
print("   E. Channel Status:")
print("      → Check if T2T Gold channel is still active on Telegram")
print("      → Verify bot still has access to the channel")
print()

print("=" * 80)

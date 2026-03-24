#!/usr/bin/env python3
"""Add a test channel to verify AI configurations."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import db

# Test channel details
CHAT_ID = "-1003018959772"
WEBHOOK = "https://discord.com/api/webhooks/1485787524499509379/fjGYWC1OSYaMSbRCgVdK-7aTfO2rx10RmqW-NMPU04s9RFBaiaiKKfC1kt_6gYkdjg8A"
NAME = "KyleTestgroup"

print("Adding test channel...")
print(f"  Name: {NAME}")
print(f"  Chat ID: {CHAT_ID}")
print(f"  Webhook: {WEBHOOK[:50]}...")

# Check if already exists
existing = db.get_channels(enabled_only=False)
if any(ch["chat_id"] == CHAT_ID for ch in existing):
    print("✗ Channel already exists!")
    sys.exit(1)

# Add channel
try:
    ch = db.add_channel(
        name=NAME,
        chat_id=CHAT_ID,
        discord_webhook=WEBHOOK,
        enabled=True,
    )
    print(f"\n✓ Channel added successfully!")
    print(f"  Channel ID: {ch['id']}")
    print(f"  Enabled: {ch['enabled']}")
    print()
    
    # Now configure AI and fallback for testing
    print("Configuring AI settings...")
    db.update_channel(
        ch['id'],
        ai_enabled=True,
        ai_provider="grok",
        ai_model="grok-4-1-fast-reasoning",
        ai_fallback_provider="google",
        ai_fallback_model="gemini-2.0-flash",
    )
    print("✓ AI configuration applied:")
    print("  Primary: grok / grok-4-1-fast-reasoning")
    print("  Fallback: google / gemini-2.0-flash")
    print()
    
    # Verify
    updated = db.get_channels(enabled_only=False)
    test_ch = next(ch for ch in updated if ch['id'] == ch['id'])
    print("✓ Final configuration:")
    print(f"  Name: {test_ch['name']}")
    print(f"  Chat ID: {test_ch['chat_id']}")
    print(f"  AI Enabled: {test_ch.get('ai_enabled')}")
    print(f"  Primary: {test_ch.get('ai_provider')} / {test_ch.get('ai_model')}")
    print(f"  Fallback: {test_ch.get('ai_fallback_provider')} / {test_ch.get('ai_fallback_model')}")
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

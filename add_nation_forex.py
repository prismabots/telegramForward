#!/usr/bin/env python3
"""Add Nation Forex channel with same config as T2T Gold."""
import db

channels = db.get_channels(enabled_only=False)

# Get T2T Gold as the template
t2t = next((ch for ch in channels if 'T2T' in ch['name']), None)
if not t2t:
    print("ERROR: T2T Gold not found")
    exit(1)

print("T2T Gold template config:")
print(f"  AI Provider: {t2t.get('ai_provider')}")
print(f"  AI Model: {t2t.get('ai_model')}")
print(f"  AI Fallback Provider: {t2t.get('ai_fallback_provider')}")
print(f"  AI Fallback Model: {t2t.get('ai_fallback_model')}")
print(f"  Triage Prompt: {'SET' if t2t.get('ai_triage_prompt') else 'NOT SET'}")
print(f"  Format Prompt: {'SET' if t2t.get('ai_format_prompt') else 'NOT SET'}")
print()

# Check if Nation Forex already exists
existing = next((ch for ch in channels if ch['chat_id'] == '-1001643237407'), None)
if existing:
    print(f"Channel already exists: ID {existing['id']} - {existing['name']}")
    exit(0)

# Add the new channel
print("Adding Nation Forex channel...")
new_ch = db.add_channel(
    name="Nation Forex",
    chat_id="-1001643237407",
    discord_webhook="https://discord.com/api/webhooks/1486788723122114750/w2hUEaTs26JnJ9oDCy2WB3Rjx8RDUrj2iX3TEYCniyRTxp-nsI1yz1FPr8jimhBG4qnJ",
)
new_id = new_ch['id']
print(f"  Created channel ID: {new_id}")

# Apply same AI config as T2T Gold
db.update_channel(
    new_id,
    ai_enabled=True,
    ai_provider=t2t.get('ai_provider'),
    ai_model=t2t.get('ai_model'),
    ai_fallback_provider=t2t.get('ai_fallback_provider'),
    ai_fallback_model=t2t.get('ai_fallback_model'),
    ai_triage_prompt=t2t.get('ai_triage_prompt'),
    ai_format_prompt=t2t.get('ai_format_prompt'),
)

# Verify
channels = db.get_channels(enabled_only=False)
verified = next((ch for ch in channels if ch['id'] == new_id), None)
if not verified:
    print("ERROR: Could not verify channel after creation")
    exit(1)
print()
print("✓ Nation Forex channel created:")
print(f"  ID: {verified['id']}")
print(f"  Name: {verified['name']}")
print(f"  Chat ID: {verified['chat_id']}")
print(f"  AI Enabled: {verified['ai_enabled']}")
print(f"  Primary: {verified.get('ai_provider') or '(global/Grok)'} / {verified.get('ai_model') or '(default)'}")
print(f"  Fallback: {verified.get('ai_fallback_provider')} / {verified.get('ai_fallback_model')}")
print(f"  Triage Prompt: {'SET' if verified.get('ai_triage_prompt') else 'NOT SET'}")
print(f"  Format Prompt: {'SET' if verified.get('ai_format_prompt') else 'NOT SET'}")
print(f"  Discord Webhook: {verified['discord_webhook'][:60]}...")

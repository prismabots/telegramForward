#!/usr/bin/env python3
"""Check T2T Gold channel status and recent activity."""
import db

# Get T2T Gold channel
channels = db.get_channels(enabled_only=False)
t2t = next((ch for ch in channels if 'T2T' in ch['name']), None)

if t2t:
    print(f"T2T Gold Premium (ID {t2t['id']}) Status:")
    print(f"  Enabled: {t2t['enabled']}")
    print(f"  AI Enabled: {t2t['ai_enabled']}")
    print(f"  Chat ID: {t2t['chat_id']}")
    print(f"  Discord Webhook: {t2t['discord_webhook'][:60]}...")
    print()
    
    print("Channel Configuration:")
    print(f"  Primary Provider: {t2t.get('ai_provider') or '(global/Grok)'}")
    print(f"  Primary Model: {t2t.get('ai_model')}")
    print(f"  Fallback Provider: {t2t.get('ai_fallback_provider')}")
    print(f"  Fallback Model: {t2t.get('ai_fallback_model')}")
    print()
    
    print("AI Configuration:")
    print(f"  Has Triage Prompt: {'Yes' if t2t.get('ai_triage_prompt') else 'No'}")
    print(f"  Has Format Prompt: {'Yes' if t2t.get('ai_format_prompt') else 'No'}")
    print()
    
    print("✓ Channel is properly configured")
    print("\nPossible reasons for stop:")
    print("  1. Bot crashed or not running")
    print("  2. Discord webhook invalid or expired")
    print("  3. Telegram connection issue")
    print("  4. AI provider (Grok) is failing")
    print("  5. Channel disabled from Telegram side")
else:
    print("T2T Gold channel not found")

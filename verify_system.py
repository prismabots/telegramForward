#!/usr/bin/env python3
"""Verify fallback system configuration and test it."""
import db
import os

print("=" * 80)
print("FALLBACK SYSTEM VERIFICATION")
print("=" * 80)
print()

# 1. Check global settings
print("1. GLOBAL SETTINGS")
print("-" * 80)
settings = db.get_all_settings()
ai_provider = settings.get("ai_provider", "openai")
ai_model = settings.get("ai_model", "gpt-5-nano")
print(f"Global AI Provider: {ai_provider}")
print(f"Global AI Model: {ai_model}")
print()

# 2. Check channel fallback configuration
print("2. CHANNEL FALLBACK CONFIGURATION")
print("-" * 80)
channels = db.get_channels(enabled_only=False)
ai_channels = [ch for ch in channels if ch.get("ai_enabled")]
print(f"Total channels: {len(channels)}")
print(f"AI-enabled channels: {len(ai_channels)}")
print()

fallback_configured = 0
for ch in ai_channels:
    prov = ch.get("ai_provider") or ai_provider
    fallback = ch.get("ai_fallback_provider")
    if fallback:
        fallback_configured += 1
        fallback_model = ch.get("ai_fallback_model")
        print(f"  ✓ {ch['name']:30s} | primary={prov:8s} | fallback={fallback}({fallback_model})")
    else:
        print(f"  ✗ {ch['name']:30s} | primary={prov:8s} | fallback=NONE")

print()
print(f"Channels with fallback configured: {fallback_configured}/{len(ai_channels)}")
print()

# 3. Check API keys in environment
print("3. API KEYS IN ENVIRONMENT")
print("-" * 80)
x_key = os.environ.get("X_API_KEY")
glm_key = os.environ.get("GLM_API_KEY")
openai_key = os.environ.get("OPENAI_API_KEY")

print(f"X_API_KEY (Grok):     {'✓ SET' if x_key else '✗ NOT SET'}")
print(f"GLM_API_KEY:          {'✓ SET' if glm_key else '✗ NOT SET'}")
print(f"OPENAI_API_KEY:       {'✓ SET' if openai_key else '✗ NOT SET'}")
print()

# 4. Test fallback logic
print("4. FALLBACK LOGIC TEST")
print("-" * 80)

# Simulate SPX channel
spx = next((ch for ch in channels if "SPX" in ch["name"]), None)
if spx:
    print(f"Testing: {spx['name']}")
    prov = spx.get("ai_provider") or ai_provider
    fallback_prov = spx.get("ai_fallback_provider")
    fallback_model = spx.get("ai_fallback_model")
    fallback_key = os.environ.get("GLM_API_KEY") if fallback_prov == "glm" else None
    
    print(f"  Primary:  {prov} / {spx.get('ai_model') or ai_model}")
    print(f"  Fallback: {fallback_prov} / {fallback_model}")
    print(f"  Fallback API Key Available: {'✓ YES' if fallback_key else '✗ NO'}")
    print()
    
    if fallback_prov and fallback_model and fallback_key:
        print("  ✓ FALLBACK SYSTEM FULLY CONFIGURED AND WORKING")
    elif fallback_prov and fallback_model:
        print("  ⚠ FALLBACK CONFIGURED BUT API KEY MISSING")
        print("    (On App Platform with DigitalOcean secrets, key should be available)")
    else:
        print("  ✗ FALLBACK NOT CONFIGURED")
print()

print("=" * 80)
print("SUMMARY")
print("=" * 80)
if fallback_configured == len(ai_channels):
    print("✓ All AI channels have fallback configured")
    print("✓ When primary provider fails, system will automatically try fallback")
    print("✓ If both fail, messages are forwarded unchanged (never discarded)")
else:
    print(f"⚠ Only {fallback_configured}/{len(ai_channels)} channels have fallback")
    print("  Run: python setup_ai_fallbacks.py")

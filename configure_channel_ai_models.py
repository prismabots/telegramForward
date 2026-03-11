"""
Configure per-channel AI models:
- GLM-4.7-Flprint("\n🚀 Grok-4-1-fast-reasoning Model (premium for SPX):")
for ch_id in grok_channels:
    try:
        channels = db.get_channels(enabled_only=False)
        ch = next((c for c in channels if c['id'] == ch_id), None)
        if ch:
            db.update_channel(
                channel_id=ch_id,
                ai_provider="grok",
                ai_model="grok-4-1-fast-reasoning"
            )
            print(f"  ✓ [{ch_id}] {ch['name']} → Grok grok-4-1-fast-reasoning")
        else:
            print(f"  ✗ [{ch_id}] Not found")
    except Exception as e:
        print(f"  ✗ [{ch_id}] Error: {e}")Forex channels (high volume, cost-effective)
- Grok for SPX Options (low volume, premium quality)
"""
import db
from load_env import load_environment

load_environment()

print("\n" + "="*70)
print("CONFIGURING PER-CHANNEL AI MODELS")
print("="*70)

# GLM channels (high volume crypto/forex)
glm_channels = [
    3,   # VIP Premium Zone (crypto)
    2,   # Forex trading
    7,   # Okako Trading Signals
    8,   # Forex Hints
    9,   # PBFX Elite
    10,  # GFR Analysis
    11,  # ADK
    15,  # T2T Gold Premium
    5,   # France Trading Pro Gold & Oil
    12,  # Superlative Fx
    14,  # Algo Pro
]

# Grok channel (low volume SPX options)
grok_channels = [
    13,  # Control Optional SPX
]

print("\n📊 GLM-4.7-FlashX Model (cost-effective for high volume):")
for ch_id in glm_channels:
    try:
        channels = db.get_channels(enabled_only=False)
        ch = next((c for c in channels if c['id'] == ch_id), None)
        if ch:
            db.update_channel(
                channel_id=ch_id,
                ai_provider="glm",
                ai_model="GLM-4.7-FlashX"
            )
            print(f"  ✓ [{ch_id}] {ch['name']} → GLM GLM-4.7-FlashX")
        else:
            print(f"  ✗ [{ch_id}] Not found")
    except Exception as e:
        print(f"  ✗ [{ch_id}] Error: {e}")

print("\n🚀 Grok-4-1-fast-reasoning Model (premium for SPX):")
for ch_id in grok_channels:
    try:
        channels = db.get_channels(enabled_only=False)
        ch = next((c for c in channels if c['id'] == ch_id), None)
        if ch:
            db.update_channel(
                channel_id=ch_id,
                ai_provider="grok",
                ai_model="grok-4-1-fast-reasoning"
            )
            print(f"  ✓ [{ch_id}] {ch['name']} → Grok grok-4-1-fast-reasoning")
        else:
            print(f"  ✗ [{ch_id}] Not found")
    except Exception as e:
        print(f"  ✗ [{ch_id}] Error: {e}")

print("\n" + "="*70)
print("✅ CONFIGURATION COMPLETE")
print("="*70)
print("\nModel Assignment:")
print(f"  • GLM-4.7-FlashX:           {len(glm_channels)} channels (crypto/forex)")
print(f"  • Grok-4-1-fast-reasoning:  {len(grok_channels)} channel (SPX options)")
print("\nAPI Keys (from environment variables):")
print("  • GLM:  Uses GLM_API_KEY from DigitalOcean env")
print("  • Grok: Uses X_API_KEY from DigitalOcean env")
print("\nNext: Restart bot to apply changes (git push or manual restart)")
print("✅ CONFIGURATION COMPLETE")
print("="*70)

print("\n📝 Summary:")
print(f"  • {len(glm_channels)} channels using GLM (high volume)")
print(f"  • {len(grok_channels)} channel using Grok (low volume)")

print("\n🔑 API Keys (from environment):")
print("  • GLM:  GLM_API_KEY")
print("  • Grok: X_API_KEY")

print("\n⚠️  IMPORTANT:")
print("  Make sure GLM_API_KEY is set in DigitalOcean environment!")
print("  Bot needs restart to apply changes.")

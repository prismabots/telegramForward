"""
Switch AI provider to Grok-4.1-fast

This script updates the global AI settings to use xAI's Grok model
for better Arabic→English translation and instruction following.
"""
import db
from load_env import load_environment
import os

load_environment()

print("\n" + "="*60)
print("SWITCHING TO GROK-4.1-FAST")
print("="*60)

# Check for X_API_KEY
x_api_key = os.getenv("X_API_KEY")
if not x_api_key:
    print("\n⚠️  X_API_KEY not found in local .env file")
    print("   (This is OK - it's set on DigitalOcean)")
    print("\nPlease enter your xAI API key (or press Enter to use existing key from DB):")
    x_api_key = input("X_API_KEY: ").strip()
    if not x_api_key:
        print("\n📝 Will keep existing API key from database")
        x_api_key = None
else:
    print(f"\n✅ X_API_KEY found: {x_api_key[:10]}...{x_api_key[-4:]}")

# Update settings
try:
    db.set_setting("ai_provider", "grok")
    db.set_setting("ai_model", "grok-4.1-fast")
    if x_api_key:
        db.set_setting("ai_api_key", x_api_key)
        print("\n✅ AI settings updated:")
        print("   Provider: grok")
        print("   Model:    grok-4.1-fast")
        print("   API Key:  [updated]")
    else:
        print("\n✅ AI settings updated:")
        print("   Provider: grok")
        print("   Model:    grok-4.1-fast")
        print("   API Key:  [keeping existing key from DB]")
    
    # Verify
    settings = db.get_all_settings()
    print("\n📊 Verification:")
    print(f"   ai_provider: {settings.get('ai_provider')}")
    print(f"   ai_model:    {settings.get('ai_model')}")
    print(f"   ai_api_key:  {settings.get('ai_api_key', '')[:10]}...")
    
    print("\n" + "="*60)
    print("✅ SWITCH COMPLETE")
    print("="*60)
    print("\nNext steps:")
    print("1. Bot will auto-reload settings on next message")
    print("2. Send a test message with Arabic content")
    print("3. Check if translation is now 100% English")
    print("\nIf issues persist, we can try:")
    print("- grok-4.1 (non-fast, more accurate)")
    print("- sonar (alternative provider)")
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    exit(1)

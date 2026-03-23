"""
Disable AI for Algo Pro channel (ID 14) in preparation for new custom prompts.
"""
import db

channel_id = 14

print("=" * 70)
print("Disabling AI for Algo Pro (Channel 14)")
print("=" * 70)

try:
    result = db.update_channel(
        channel_id=channel_id,
        ai_enabled=False,
        ai_triage_prompt=None,
        ai_format_prompt=None
    )
    
    if result:
        print(f"\n✅ AI disabled for '{result['name']}' (ID {result['id']})")
        print(f"   Channel is ready for new custom prompts")
        print(f"   Status: AI processing turned OFF")
    else:
        print(f"\n❌ ERROR: Channel ID {channel_id} not found")

except Exception as e:
    print(f"\n❌ ERROR: {e}")

print("\n" + "=" * 70)
print("Ready for new Algo Pro prompts!")
print("=" * 70)

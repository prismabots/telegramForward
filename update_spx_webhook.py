"""
Update webhook for SPX Options channel (channel 13)
"""
import db
from load_env import load_environment

load_environment()

new_webhook = "https://discord.com/api/webhooks/1481361206957572137/9zQO7E7drjuKDxTxBvTImppUxHO6Ue1clZkC69mqrOEta9i_xwssfrTStK9327esA98L"

print("\n" + "="*70)
print("UPDATING SPX OPTIONS WEBHOOK")
print("="*70)

try:
    # Get current channel info
    channels = db.get_channels(enabled_only=False)
    channel = next((ch for ch in channels if ch['id'] == 13), None)
    
    if not channel:
        print("❌ Channel 13 not found!")
        exit(1)
    
    print(f"\nChannel: {channel['name']}")
    print(f"Old webhook: {channel['discord_webhook'][:50]}...")
    print(f"New webhook: {new_webhook[:50]}...")
    
    # Update webhook
    db.update_channel(
        channel_id=13,
        discord_webhook=new_webhook
    )
    
    # Verify
    channels = db.get_channels(enabled_only=False)
    updated = next((ch for ch in channels if ch['id'] == 13), None)
    if updated:
        print("\n✅ Webhook updated successfully!")
        print(f"Verified: {updated['discord_webhook'][:50]}...")
    else:
        print("\n⚠️ Could not verify update")
    
    print("\n" + "="*70)
    print("✅ COMPLETE")
    print("="*70)
    print("\nBot will use new webhook on next message.")
    print("No restart needed - config reloads automatically.")
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    exit(1)

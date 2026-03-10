"""
Disable message logging for all channels except specified ones.
"""
import db

# Channels that should KEEP logging enabled
keep_logging = [13, 14]  # Control Optional SPX, Algo Pro

# Get all channels
channels = db.get_channels(enabled_only=False)

print("="*70)
print("Disabling Message Logging for Channels")
print("="*70)

disable_count = 0
keep_count = 0

for ch in channels:
    ch_id = ch['id']
    name = ch['name']
    
    if ch_id in keep_logging:
        print(f"✓ [{ch_id}] {name} - KEEPING logging enabled")
        keep_count += 1
    else:
        # Disable logging for this channel
        try:
            result = db.update_channel(
                channel_id=ch_id,
                log_messages=False
            )
            if result:
                print(f"✗ [{ch_id}] {name} - Logging DISABLED")
                disable_count += 1
            else:
                print(f"⚠ [{ch_id}] {name} - Failed to update")
        except Exception as e:
            print(f"❌ [{ch_id}] {name} - Error: {e}")

print("\n" + "="*70)
print(f"Summary:")
print(f"  Logging DISABLED: {disable_count} channels")
print(f"  Logging ENABLED:  {keep_count} channels")
print("="*70)

"""
Apply Trading Signals prompts to all crypto trading channels
"""
import db
from load_env import load_environment

# Load environment variables
load_environment()

# Read the prompt files
with open('prompts/triage_trading_signals.txt', 'r', encoding='utf-8') as f:
    triage_prompt = f.read()

with open('prompts/format_trading_signals.txt', 'r', encoding='utf-8') as f:
    format_prompt = f.read()

# Get all channels and find ones using trading signals
print("\n" + "="*70)
print("Finding channels with trading signal AI...")
print("="*70)

channels = db.get_channels(enabled_only=False)
trading_channels = []

for ch in channels:
    # Check if channel uses trading signals triage
    if ch.get('ai_triage_prompt') and 'trading signal filter' in ch.get('ai_triage_prompt', '').lower():
        trading_channels.append(ch)
        print(f"  ✓ [{ch['id']}] {ch['name']}")

if not trading_channels:
    print("  ✗ No channels found using trading signals prompts")
    exit(1)

print(f"\nFound {len(trading_channels)} trading signal channel(s)")
print("\n" + "="*70)
print("Updating channels...")
print("="*70)

success_count = 0
for ch in trading_channels:
    try:
        db.update_channel(
            channel_id=ch['id'],
            ai_triage_prompt=triage_prompt,
            ai_format_prompt=format_prompt,
        )
        print(f"  ✓ [{ch['id']}] {ch['name']}")
        success_count += 1
    except Exception as e:
        print(f"  ✗ [{ch['id']}] {ch['name']}: {e}")

print("\n" + "="*70)
print(f"✅ Successfully updated {success_count}/{len(trading_channels)} channels")
print("="*70)
print("\nChanges applied:")
print("- Strengthened @mention removal (CRITICAL rule)")
print("- Added explicit 'ALL channel/bot references' removal")
print("- Added example showing @DigiLeakBot removal")
print("\nBot will use updated prompts on next message!")

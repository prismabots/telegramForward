"""
Apply FOREX/Gold AI prompts to multiple channels at once.
"""
import db

# Read the prompt files
with open('prompts/triage_forex_gold.txt', 'r', encoding='utf-8') as f:
    triage_prompt = f.read()

with open('prompts/format_forex_gold.txt', 'r', encoding='utf-8') as f:
    format_prompt = f.read()

# Channels to update
channel_ids = [15, 2, 7, 8, 9, 10, 11, 14]
channel_names = {
    15: "T2T Gold Premium",
    2: "Forex trading",
    7: "Okako Trading Signals",
    8: "Forex Hints",
    9: "PBFX Elite",
    10: "GFR Analysis",
    11: "ADK",
    14: "Algo Pro"
}

print("="*70)
print("Applying FOREX/Gold AI Triage to Multiple Channels")
print("="*70)

success_count = 0
for channel_id in channel_ids:
    name = channel_names.get(channel_id, f"ID {channel_id}")
    print(f"\n[{channel_id}] {name}...")
    
    try:
        result = db.update_channel(
            channel_id=channel_id,
            ai_enabled=True,
            ai_triage_prompt=triage_prompt,
            ai_format_prompt=format_prompt
        )
        
        if result:
            print(f"    ✓ AI enabled with FOREX/Gold prompts")
            success_count += 1
        else:
            print(f"    ✗ Failed to update (channel not found?)")
    
    except Exception as e:
        print(f"    ✗ Error: {e}")

print("\n" + "="*70)
print(f"✅ Successfully enabled AI on {success_count}/{len(channel_ids)} channels")
print("="*70)

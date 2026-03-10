import db

channels = db.get_channels(enabled_only=False)

print("\n" + "="*70)
print("ALL CHANNELS - AI Triage Status")
print("="*70)
print(f"{'ID':<5} {'Channel Name':<35} {'AI Enabled':<15}")
print("-"*70)

for ch in channels:
    ch_id = str(ch['id'])
    name = ch['name'][:33]
    ai_status = "✓ YES" if ch.get('ai_enabled') else "✗ NO"
    
    # Show which prompts if AI is enabled
    if ch.get('ai_enabled'):
        triage = "custom" if ch.get('ai_triage_prompt') else "default"
        format_p = "custom" if ch.get('ai_format_prompt') else "default"
        ai_status = f"✓ YES ({triage}/{format_p})"
    
    print(f"{ch_id:<5} {name:<35} {ai_status}")

print("="*70)
print(f"\nTotal: {len(channels)} channels")
print("\nLegend:")
print("  ✓ YES (custom/custom) = AI enabled with custom prompts")
print("  ✓ YES (default/default) = AI enabled with default prompts")
print("  ✗ NO = AI disabled")

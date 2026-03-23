"""Quick verification that channel 13 is configured with SPX Options AI"""
import db

channel = None
for c in db.get_channels(enabled_only=False):
    if c['id'] == 13:
        channel = c
        break

if channel:
    print(f"✅ Channel 13 Configuration Verified:\n")
    print(f"   Name: {channel['name']}")
    print(f"   AI Enabled: {channel['ai_enabled']}")
    print(f"   Triage Prompt: {len(channel['ai_triage_prompt'])} characters")
    print(f"   Format Prompt: {len(channel['ai_format_prompt'])} characters")
    print(f"   Status: {'Enabled' if channel['enabled'] else 'Disabled'}")
    
    # Show first 100 chars of each prompt to verify it's SPX-specific
    if channel['ai_triage_prompt']:
        preview = channel['ai_triage_prompt'][:150]
        print(f"\n   Triage Preview: {preview}...")
else:
    print("❌ Channel 13 not found")

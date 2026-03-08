"""
Apply custom French trading prompts to France Trading Pro channel.
"""
import db
import sys

# Read the prompt files
with open('prompts/triage_french_trading.txt', 'r', encoding='utf-8') as f:
    TRIAGE_PROMPT = f.read()

with open('prompts/format_french_trading.txt', 'r', encoding='utf-8') as f:
    FORMAT_PROMPT = f.read()

def main():
    if len(sys.argv) < 2:
        print("Usage: python apply_french_prompts.py <channel_id>")
        print("Example: python apply_french_prompts.py 5")
        sys.exit(1)
    
    channel_id = int(sys.argv[1])
    
    # Get channel info
    channels = db.get_channels(enabled_only=False)
    channel = next((ch for ch in channels if ch['id'] == channel_id), None)
    
    if not channel:
        print(f"❌ Channel ID {channel_id} not found")
        sys.exit(1)
    
    channel_name = channel['name']
    print(f"Applying French trading prompts to '{channel_name}' (ID {channel_id})...")
    
    # Update channel with AI prompts
    db.update_channel(
        channel_id,
        ai_enabled=True,
        ai_triage_prompt=TRIAGE_PROMPT,
        ai_format_prompt=FORMAT_PROMPT,
    )
    
    print(f"✓ AI triage enabled for '{channel_name}' (ID {channel_id})")
    print("  - Triage: Custom French trading signal filter")
    print("  - Format: French to English translation with signal formatting")

if __name__ == "__main__":
    main()

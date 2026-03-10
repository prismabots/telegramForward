"""
apply_spx_options_prompts.py — Apply SPX Options AI prompts to channel 13

This script configures AI triage and formatting for the SPX Options channel (channel 13).
It handles Arabic/English content, options terminology, and filters promotional content.

Usage:
    python apply_spx_options_prompts.py

The script will:
1. Load custom triage and format prompts from prompts/
2. Apply them to channel 13 (Control Optional SPX)
3. Enable AI processing for that channel
"""

import sys
import os
import db

# Load prompts from files
PROMPTS_DIR = os.path.join(os.path.dirname(__file__), "prompts")

with open(os.path.join(PROMPTS_DIR, "triage_spx_options.txt"), "r", encoding="utf-8") as f:
    TRIAGE_PROMPT = f.read().strip()

with open(os.path.join(PROMPTS_DIR, "format_spx_options.txt"), "r", encoding="utf-8") as f:
    FORMAT_PROMPT = f.read().strip()


def apply_to_channel(channel_id: int):
    """Apply SPX Options prompts to specified channel."""
    print(f"Applying SPX Options AI prompts to channel {channel_id}...")
    
    result = db.update_channel(
        channel_id,
        ai_enabled=True,
        ai_triage_prompt=TRIAGE_PROMPT,
        ai_format_prompt=FORMAT_PROMPT,
    )
    
    if result:
        print(f"✅ AI triage enabled for '{result['name']}' (ID {result['id']})")
        print(f"  • Triage: SPX Options signal filter with Arabic support")
        print(f"  • Format: Clean Discord formatter for options signals")
        print(f"  • Features: Translation, promotional filtering, options terminology")
    else:
        print(f"❌ ERROR: Channel ID {channel_id} not found")
        sys.exit(1)


if __name__ == "__main__":
    # Check environment
    if not os.environ.get("BACKUP_DB_ADMIN_URL"):
        print("❌ ERROR: BACKUP_DB_ADMIN_URL environment variable not set")
        print("   This script requires database access to update channel settings.")
        sys.exit(1)
    
    # Default to channel 13 (Control Optional SPX)
    CHANNEL_ID = 13
    
    # Allow override via command line
    if len(sys.argv) > 1:
        try:
            CHANNEL_ID = int(sys.argv[1])
        except ValueError:
            print(f"❌ ERROR: Invalid channel ID '{sys.argv[1]}'")
            print("Usage: python apply_spx_options_prompts.py [channel_id]")
            sys.exit(1)
    
    print("=" * 60)
    print("SPX OPTIONS AI CONFIGURATION")
    print("=" * 60)
    
    apply_to_channel(CHANNEL_ID)
    
    print("\n" + "=" * 60)
    print("Configuration complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Restart the bot to apply changes")
    print("2. Send a test message from channel 13")
    print("3. Monitor logs for AI processing results")

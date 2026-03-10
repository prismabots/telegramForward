"""
apply_algo_pro_prompts.py — Apply custom AI prompts to Algo Pro channel (14)

This script configures AI triage and formatting for the TradeAlgo Alerts channel.
It handles stock signals, futures, market analysis, and filters motivational content.

Usage:
    python apply_algo_pro_prompts.py
"""

import sys
import os
import db

# Load prompts from files
PROMPTS_DIR = os.path.join(os.path.dirname(__file__), "prompts")

with open(os.path.join(PROMPTS_DIR, "triage_algo_pro.txt"), "r", encoding="utf-8") as f:
    TRIAGE_PROMPT = f.read().strip()

with open(os.path.join(PROMPTS_DIR, "format_algo_pro.txt"), "r", encoding="utf-8") as f:
    FORMAT_PROMPT = f.read().strip()


def apply_to_channel(channel_id: int):
    """Apply Algo Pro prompts to specified channel."""
    print(f"Applying Algo Pro AI prompts to channel {channel_id}...")
    
    result = db.update_channel(
        channel_id,
        ai_enabled=True,
        ai_triage_prompt=TRIAGE_PROMPT,
        ai_format_prompt=FORMAT_PROMPT,
    )
    
    if result:
        print(f"✅ AI triage enabled for '{result['name']}' (ID {result['id']})")
        print(f"  • Triage: TradeAlgo signal filter (stocks, futures, analysis)")
        print(f"  • Format: Clean Discord formatter for trading signals")
        print(f"  • Features: Symbol detection, analyst attribution, meme filtering")
    else:
        print(f"❌ ERROR: Channel ID {channel_id} not found")
        sys.exit(1)


if __name__ == "__main__":
    # Check environment
    if not os.environ.get("BACKUP_DB_ADMIN_URL"):
        print("❌ ERROR: BACKUP_DB_ADMIN_URL environment variable not set")
        print("   This script requires database access to update channel settings.")
        sys.exit(1)
    
    # Default to channel 14 (Algo Pro)
    CHANNEL_ID = 14
    
    # Allow override via command line
    if len(sys.argv) > 1:
        try:
            CHANNEL_ID = int(sys.argv[1])
        except ValueError:
            print(f"❌ ERROR: Invalid channel ID '{sys.argv[1]}'")
            print("Usage: python apply_algo_pro_prompts.py [channel_id]")
            sys.exit(1)
    
    print("=" * 60)
    print("ALGO PRO (TRADEALGO ALERTS) AI CONFIGURATION")
    print("=" * 60)
    
    apply_to_channel(CHANNEL_ID)
    
    print("\n" + "=" * 60)
    print("Configuration complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Restart the bot to apply changes")
    print("2. Send a test message from channel 14")
    print("3. Monitor logs for AI processing results")

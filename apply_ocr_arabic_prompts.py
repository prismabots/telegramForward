"""
apply_ocr_arabic_prompts.py — Apply the "AI with OCR for Arabic" template to a channel.

Configures a channel to:
  1. Run OCR on every image attachment (Google Cloud Vision by default).
  2. Feed the OCR text + message text into the AI for Arabic→English
     triage and formatting.

Usage:
    python apply_ocr_arabic_prompts.py [channel_id]

The script will:
  1. Load the triage/format prompts from prompts/triage_ocr_arabic.txt and
     prompts/format_ocr_arabic.txt.
  2. Apply them to the channel and enable AI.
  3. Enable OCR and set the OCR provider.
"""

import sys
import os
import db
from load_env import load_environment

load_environment()

PROMPTS_DIR = os.path.join(os.path.dirname(__file__), "prompts")

with open(os.path.join(PROMPTS_DIR, "triage_ocr_arabic.txt"), "r", encoding="utf-8") as f:
    TRIAGE_PROMPT = f.read().strip()

with open(os.path.join(PROMPTS_DIR, "format_ocr_arabic.txt"), "r", encoding="utf-8") as f:
    FORMAT_PROMPT = f.read().strip()


def apply_to_channel(channel_id: int, ocr_provider: str = "google", ocr_tier: str = "agentic"):
    """Apply the OCR+Arabic AI template to the given channel."""
    print(f"Applying 'AI with OCR for Arabic' template to channel {channel_id}...")

    result = db.update_channel(
        channel_id,
        ai_enabled=True,
        ai_triage_prompt=TRIAGE_PROMPT,
        ai_format_prompt=FORMAT_PROMPT,
        ocr_enabled=True,
        ocr_provider=ocr_provider,
        ocr_tier=ocr_tier,
    )

    if result:
        print(f"✅ Template applied to '{result['name']}' (ID {result['id']})")
        print(f"  • AI:     Arabic triage + formatter")
        print(f"  • OCR:    enabled ({ocr_provider}, tier={ocr_tier})")
        print(f"  • Flow:   image → OCR → AI → English signal")
    else:
        print(f"❌ ERROR: Channel ID {channel_id} not found")
        sys.exit(1)


if __name__ == "__main__":
    if not os.environ.get("BACKUP_DB_ADMIN_URL"):
        print("❌ ERROR: BACKUP_DB_ADMIN_URL environment variable not set")
        sys.exit(1)

    channel_id = 13
    if len(sys.argv) > 1:
        try:
            channel_id = int(sys.argv[1])
        except ValueError:
            print(f"❌ ERROR: Invalid channel ID '{sys.argv[1]}'")
            print("Usage: python apply_ocr_arabic_prompts.py [channel_id] [ocr_provider] [ocr_tier]")
            sys.exit(1)

    ocr_provider = "google"
    if len(sys.argv) > 2:
        ocr_provider = sys.argv[2]

    ocr_tier = "agentic"
    if len(sys.argv) > 3:
        ocr_tier = sys.argv[3]

    print("=" * 60)
    print("AI WITH OCR FOR ARABIC — CONFIGURATION")
    print("=" * 60)

    apply_to_channel(channel_id, ocr_provider, ocr_tier)

    print("\n" + "=" * 60)
    print("Configuration complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Ensure GOOGLE_API_KEY (or LLAMA_PARSE_API_KEY) is set in the environment")
    print("2. Restart the bot to apply changes")
    print("3. Send a test message with an image to verify OCR + AI output")

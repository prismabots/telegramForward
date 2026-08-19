"""
rollback_ch13_spx.py — Roll back the ch 13 OCR migration (migrate_ch13_ocr.py).

Restores the ORIGINAL SPX Options template on channel 13 (Control Optional SPX):
  1. Re-applies prompts/triage_spx_options.txt + prompts/format_spx_options.txt
     (the pre-OCR template that was live before the migration).
  2. Disables OCR on ch 13 (back to image-forwarding behavior).
  3. Disables suppress_images on ch 13 AND ch 22 (images flow to Discord again).

After running: restart the bot (config loads at startup).
"""

import db
from load_env import load_environment

load_environment()

with open("prompts/triage_spx_options.txt", encoding="utf-8") as f:
    TRIAGE = f.read().strip()
with open("prompts/format_spx_options.txt", encoding="utf-8") as f:
    FORMAT = f.read().strip()

r = db.update_channel(
    13,
    ai_triage_prompt=TRIAGE,
    ai_format_prompt=FORMAT,
    ocr_enabled=False,
    suppress_images=False,
)
print(f"ch 13 {r['name']}: SPX template restored, ocr={r['ocr_enabled']}, "
      f"suppress_images={r['suppress_images']}")

r = db.update_channel(22, suppress_images=False)
print(f"ch 22 {r['name']}: suppress_images={r['suppress_images']}")

print("\nRollback complete. Restart the bot to apply.")

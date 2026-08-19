"""
migrate_ch13_ocr.py — Migrate channel 13 (Control Optional SPX) to the
"AI with OCR for Arabic" template.

Why: ch 13 shares its Telegram source (controlOptionalspx) with ch 22, and the
multi-destination pipeline runs ONE shared pass driven by ch 13's config
(lowest ID wins). Migrating 13 therefore brings the OCR pipeline — and
text-only output — to BOTH destinations (SPXOption-Viper + SPXOptions-Beast).

What it does:
  1. Applies prompts/triage_ocr_arabic.txt + prompts/format_ocr_arabic.txt
     (superset of the old SPX prompts: contracts, profit updates, order-flow
     tables, annotated-chart level extraction; adds OCR text handling and
     prompt-injection guards).
  2. Enables OCR: google primary, llama_parse/fast fallback (main.py wires
     the fallback automatically).
  3. Enables suppress_images on BOTH 13 and 22 → text-only Discord output.
     (Suppression happens AFTER OCR — see main.py "deferred suppression".)

ROLLBACK:  python rollback_ch13_spx.py
  Restores the original SPX options template from
  prompts/triage_spx_options.txt + prompts/format_spx_options.txt and
  disables OCR + suppress_images on 13 and 22.
"""

import db
from load_env import load_environment

load_environment()

with open("prompts/triage_ocr_arabic.txt", encoding="utf-8") as f:
    TRIAGE = f.read().strip()
with open("prompts/format_ocr_arabic.txt", encoding="utf-8") as f:
    FORMAT = f.read().strip()

# Channel 13: swap template + enable OCR
r = db.update_channel(
    13,
    ai_enabled=True,
    ai_triage_prompt=TRIAGE,
    ai_format_prompt=FORMAT,
    ocr_enabled=True,
    ocr_provider="google",   # primary; preserves Arabic annotations (matrix-tested)
    ocr_tier="fast",         # tier used by the llama_parse fallback
    suppress_images=True,    # text-only output (runs after OCR)
)
print(f"ch 13 {r['name']}: OCR template applied, ocr={r['ocr_enabled']}, "
      f"suppress_images={r['suppress_images']}")

# Channel 22: already on the OCR template; enable suppression for consistency
# (the shared pass is driven by ch 13, but keep configs aligned).
r = db.update_channel(22, suppress_images=True)
print(f"ch 22 {r['name']}: suppress_images={r['suppress_images']}")

print("\nDone. To roll back: python rollback_ch13_spx.py")

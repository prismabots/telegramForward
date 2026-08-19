"""
test_matrix.py — 4-way OCR x AI comparison across a folder of images.

For every image, runs all four combinations:
    1. LlamaParse (fast) OCR  -> Grok
    2. LlamaParse (fast) OCR  -> Google (gemini)
    3. Google Vision OCR      -> Grok
    4. Google Vision OCR      -> Google (gemini)

OCR runs WITHOUT fallback (pure provider) so differences stay visible.
Uses the live channel prompts from the DB (default: channel 22).
Grok model defaults to the global ai_model from tele_settings (production).

Usage:
    python test_matrix.py <folder> [--channel 22] [--out matrix_results.txt]
"""

import argparse
import asyncio
import logging
import os
import sys
import time

from load_env import load_environment

load_environment()

import db  # noqa: E402
import ocr_service  # noqa: E402
from ai_services import triage_message  # noqa: E402

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"}

AI_CONFIGS = {
    "grok":   {"key_env": "X_API_KEY",     "model": None},  # model from DB settings
    "google": {"key_env": "GOOGLE_API_KEY", "model": "gemini-2.5-flash"},
}


async def run_combo(ocr_text, ch, ai_name, model, api_key):
    start = time.monotonic()
    try:
        r = await triage_message(
            message_text="",
            channel_name=ch["name"],
            triage_prompt=ch["ai_triage_prompt"],
            format_prompt=ch["ai_format_prompt"],
            provider=ai_name, model=model, api_key=api_key,
            ocr_text=ocr_text, channel_id=ch["id"], verbose_logging=False,
        )
        elapsed = time.monotonic() - start
        out = r.rewritten_text or "(unchanged)"
        return f"TRIAGE: {r.action} — {r.reason}\nFORMATTED:\n{out}\n[{ai_name} took {elapsed:.1f}s]"
    except Exception as e:
        return f"AI ERROR: {type(e).__name__}: {e}"


async def main() -> None:
    parser = argparse.ArgumentParser(description="4-way OCR x AI matrix test")
    parser.add_argument("folder", help="Folder containing images")
    parser.add_argument("--channel", type=int, default=22)
    parser.add_argument("--out", default="matrix_results.txt")
    args = parser.parse_args()

    ch = next((c for c in db.get_channels(enabled_only=False) if c["id"] == args.channel), None)
    if not ch:
        print(f"ERROR: channel {args.channel} not found"); sys.exit(1)

    grok_model = db.get_setting("ai_model", "grok-4.1-fast")
    AI_CONFIGS["grok"]["model"] = grok_model

    for name, cfg in AI_CONFIGS.items():
        if not os.environ.get(cfg["key_env"]):
            print(f"ERROR: {cfg['key_env']} not set"); sys.exit(1)

    images = sorted(
        os.path.join(args.folder, f)
        for f in os.listdir(args.folder)
        if os.path.splitext(f)[1].lower() in IMAGE_EXTS
    )
    if not images:
        print("No images found"); sys.exit(1)

    report = open(args.out, "w", encoding="utf-8")

    def emit(text=""):
        print(text)
        report.write(text + "\n")
        report.flush()

    emit(f"MATRIX TEST: {len(images)} images | channel {args.channel} ({ch['name']})")
    emit(f"AI: grok={grok_model}, google=gemini-2.5-flash")
    emit(f"OCR: pure llama_parse/fast vs pure google (no fallback)\n")

    for path in images:
        name = os.path.basename(path)
        with open(path, "rb") as f:
            data = f.read()

        emit("=" * 76)
        emit(f"IMAGE: {name}")
        emit("=" * 76)

        ocr_results = {}
        for ocr_name, kw in (("llama", {"provider": "llama_parse", "llama_tier": "fast"}),
                             ("google", {"provider": "google"})):
            start = time.monotonic()
            text = await ocr_service.extract_text_from_image(data, **kw)
            ocr_results[ocr_name] = text
            emit(f"--- OCR [{ocr_name}] {time.monotonic()-start:.1f}s, {len(text or '')} chars ---")
            emit(text or "(none)")

        for ocr_name, ocr_text in ocr_results.items():
            for ai_name, cfg in AI_CONFIGS.items():
                emit(f"\n>>> COMBO: {ocr_name} OCR -> {ai_name} AI")
                emit(await run_combo(ocr_text, ch, ai_name, cfg["model"],
                                     os.environ[cfg["key_env"]]))
        emit()

    report.close()
    print(f"\nFull report written to {args.out}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)
    asyncio.run(main())

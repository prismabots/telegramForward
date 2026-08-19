"""
test_image_batch.py — Batch-test images through the full OCR + AI pipeline.

Runs every image in a folder through the exact production path for the OCR
Arabic channels (20/21/22):
  image → OCR (llama_parse/fast, google fallback) → watermark filter
        → triage (channel 22 prompts, live from DB) → format

Prints a compact report per image so you can judge which content types
(contracts, tables, charts) are worth forwarding as text-only.

Usage:
    python test_image_batch.py <folder> [--channel 22] [--provider google]
                                      [--model gemini-2.5-flash]

Example:
    python test_image_batch.py test_images/
"""

import argparse
import asyncio
import logging
import os
import sys

from load_env import load_environment

load_environment()

import db  # noqa: E402
import ocr_service  # noqa: E402
from ai_services import triage_message  # noqa: E402

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"}

# Map AI provider -> env var holding its key (mirrors main.py)
AI_KEY_ENV = {
    "openai": "OPENAI_API_KEY",
    "google": "GOOGLE_API_KEY",
    "grok": "X_API_KEY",
    "glm": "GLM_API_KEY",
    "deepseek": "DEEPSEEK_API_KEY",
    "sonar": "SONAR_API_KEY",
}


async def process_image(path: str, ch: dict, provider: str, model: str, api_key: str) -> None:
    name = os.path.basename(path)
    with open(path, "rb") as f:
        image_bytes = f.read()

    ocr_text = await ocr_service.extract_text_from_image(
        image_bytes,
        provider=ch.get("ocr_provider") or "llama_parse",
        llama_tier=ch.get("ocr_tier") or "fast",
        fallback_provider="google",
    )

    print("=" * 72)
    print(f"IMAGE: {name}  ({len(image_bytes)} bytes)")
    print("=" * 72)
    print(f"OCR ({len(ocr_text or '')} chars):")
    print(ocr_text or "(none)")

    result = await triage_message(
        message_text="",
        channel_name=ch["name"],
        triage_prompt=ch["ai_triage_prompt"],
        format_prompt=ch["ai_format_prompt"],
        provider=provider,
        model=model,
        api_key=api_key,
        ocr_text=ocr_text,
        channel_id=ch["id"],
        verbose_logging=False,
    )
    print(f"\nTRIAGE: {result.action} — {result.reason}")
    if result.action == "forward":
        print("FORMATTED:")
        print(result.rewritten_text or "(unchanged)")
    print()


async def main() -> None:
    parser = argparse.ArgumentParser(description="Batch-test images through OCR + AI pipeline")
    parser.add_argument("folder", help="Folder containing images to test")
    parser.add_argument("--channel", type=int, default=22,
                        help="Channel ID whose prompts/OCR config to use (default: 22)")
    parser.add_argument("--provider", default="google", help="AI provider (default: google)")
    parser.add_argument("--model", default="gemini-2.5-flash", help="AI model (default: gemini-2.5-flash)")
    args = parser.parse_args()

    api_key = os.environ.get(AI_KEY_ENV.get(args.provider, ""), "")
    if not api_key:
        print(f"ERROR: no API key for provider '{args.provider}' "
              f"(expected env var {AI_KEY_ENV.get(args.provider, '?')})")
        sys.exit(1)

    channels = [c for c in db.get_channels(enabled_only=False) if c["id"] == args.channel]
    if not channels:
        print(f"ERROR: channel {args.channel} not found in DB")
        sys.exit(1)
    ch = channels[0]

    images = sorted(
        os.path.join(args.folder, f)
        for f in os.listdir(args.folder)
        if os.path.splitext(f)[1].lower() in IMAGE_EXTS
    )
    if not images:
        print(f"No images found in {args.folder}")
        sys.exit(1)

    print(f"Testing {len(images)} image(s) with channel {args.channel} config "
          f"({ch['name']}), AI={args.provider}/{args.model}\n")

    for path in images:
        try:
            await process_image(path, ch, args.provider, args.model, api_key)
        except Exception as e:
            print(f"ERROR processing {path}: {type(e).__name__}: {e}\n")


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)
    asyncio.run(main())

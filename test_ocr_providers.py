"""
test_ocr_providers.py — Compare OCR providers/tiers on a single image.

Runs the same image through every available OCR configuration and prints
timing + extracted text side by side, so you can pick the config that
reads Arabic contract/chart images best.

Usage:
    python test_ocr_providers.py <image_path>
    python test_ocr_providers.py chart.png --configs google llama_fast llama_agentic

Configs:
    google               Google Cloud Vision TEXT_DETECTION  (GOOGLE_API_KEY)
    llama_fast           LlamaParse tier=fast                (LLAMA_PARSE_API_KEY)
    llama_cost_effective LlamaParse tier=cost_effective
    llama_agentic        LlamaParse tier=agentic
    llama_agentic_plus   LlamaParse tier=agentic_plus
"""

import argparse
import asyncio
import logging
import os
import time

from load_env import load_environment

load_environment()

import ocr_service  # noqa: E402

logging.basicConfig(level=logging.INFO, format="  [ocr] %(message)s")

CONFIGS = {
    "google":               {"provider": "google",      "llama_tier": "agentic"},
    "llama_fast":           {"provider": "llama_parse", "llama_tier": "fast"},
    "llama_cost_effective": {"provider": "llama_parse", "llama_tier": "cost_effective"},
    "llama_agentic":        {"provider": "llama_parse", "llama_tier": "agentic"},
    "llama_agentic_plus":   {"provider": "llama_parse", "llama_tier": "agentic_plus"},
}

REQUIRED_KEY = {"google": "GOOGLE_API_KEY", "llama_parse": "LLAMA_PARSE_API_KEY"}


async def run_one(name: str, cfg: dict, image_bytes: bytes, timeout: float) -> None:
    key_name = REQUIRED_KEY[cfg["provider"]]
    print("=" * 72)
    print(f"CONFIG: {name}  (provider={cfg['provider']}, tier={cfg['llama_tier']})")
    print("=" * 72)
    if not os.environ.get(key_name):
        print(f"SKIPPED — {key_name} not set in environment\n")
        return

    start = time.monotonic()
    task = asyncio.create_task(
        ocr_service.extract_text_from_image(
            image_bytes, provider=cfg["provider"], llama_tier=cfg["llama_tier"]
        )
    )
    while not task.done():
        done, _ = await asyncio.wait({task}, timeout=15)
        if done:
            break
        elapsed = time.monotonic() - start
        if elapsed > timeout:
            task.cancel()
            print(f"TIMEOUT after {elapsed:.0f}s — job did not finish in time\n")
            return
        print(f"  ... still running ({elapsed:.0f}s elapsed)", flush=True)

    elapsed = time.monotonic() - start
    try:
        text = task.result()
    except Exception as e:
        print(f"FAILED after {elapsed:.1f}s — {type(e).__name__}: {e}\n")
        return

    if text is None:
        print(f"FAILED after {elapsed:.1f}s — no text returned (see warnings above)\n")
        return

    print(f"OK in {elapsed:.1f}s — {len(text)} chars")
    print("-" * 72)
    print(text)
    print()


async def main() -> None:
    parser = argparse.ArgumentParser(description="Compare OCR providers/tiers on one image")
    parser.add_argument("image", help="Path to the image file to test")
    parser.add_argument(
        "--configs", nargs="*", default=list(CONFIGS), choices=list(CONFIGS),
        help="Subset of configs to run (default: all)",
    )
    parser.add_argument(
        "--timeout", type=float, default=360,
        help="Max seconds to wait per config before giving up (default: 360)",
    )
    args = parser.parse_args()

    with open(args.image, "rb") as f:
        image_bytes = f.read()
    print(f"Image: {args.image} ({len(image_bytes)} bytes)\n")

    for name in args.configs:
        await run_one(name, CONFIGS[name], image_bytes, args.timeout)


if __name__ == "__main__":
    asyncio.run(main())

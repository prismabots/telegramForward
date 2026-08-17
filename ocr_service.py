"""
ocr_service.py — Reusable OCR layer for telegramForward.

Extracts text from an image via a pluggable provider so that any processing
template can read text embedded in images (e.g. the "AI with OCR for Arabic"
template). Keep this module dependency-light and side-effect free so other
templates can import it without pulling in the Telegram/Discord stack.

Supported providers:
  - google        Google Cloud Vision (TEXT_DETECTION)
  - llama_parse   LlamaParse REST v2 (upload + poll)

Environment variables:
  GOOGLE_API_KEY        required when provider == "google"
  LLAMA_PARSE_API_KEY   required when provider == "llama_parse"
"""

import os
import json
import base64
import asyncio
import logging

import aiohttp

logger = logging.getLogger(__name__)

GOOGLE_VISION_URL = "https://vision.googleapis.com/v1/images:annotate"
LLAMA_PARSE_BASE = "https://api.cloud.llamaindex.ai"


async def extract_text_from_image(
    image_data: bytes,
    provider: str = "google",
    llama_tier: str = "agentic",
) -> str | None:
    """Extract text from image bytes using the selected OCR provider.

    Returns the extracted text, or ``None`` on any failure (never raises).
    """
    provider = (provider or "google").lower()
    if provider == "llama_parse":
        return await _ocr_llama_parse(image_data, tier=llama_tier)
    return await _ocr_google_vision(image_data)


async def _ocr_google_vision(image_data: bytes) -> str | None:
    api_key = os.environ.get("GOOGLE_API_KEY", "")
    if not api_key:
        logger.warning("GOOGLE_API_KEY not set — Google Vision OCR unavailable")
        return None

    payload = {
        "requests": [
            {
                "image": {"content": base64.b64encode(image_data).decode("ascii")},
                "features": [{"type": "TEXT_DETECTION", "maxResults": 1}],
            }
        ]
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{GOOGLE_VISION_URL}?key={api_key}",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp:
                if resp.status != 200:
                    logger.warning(
                        f"Google Vision OCR error {resp.status}: {await resp.text()}"
                    )
                    return None
                data = await resp.json()

        annotations = (data.get("responses") or [{}])[0].get("textAnnotations") or []
        if annotations:
            return annotations[0].get("description")
        return None
    except Exception as e:
        logger.warning(f"Google Vision OCR failed: {e}")
        return None


async def _ocr_llama_parse(image_data: bytes, tier: str = "agentic") -> str | None:
    api_key = os.environ.get("LLAMA_PARSE_API_KEY", "")
    if not api_key:
        logger.warning("LLAMA_PARSE_API_KEY not set — LlamaParse OCR unavailable")
        return None

    filename = _sniff_image_filename(image_data)
    headers = {"Authorization": f"Bearer {api_key}"}

    try:
        async with aiohttp.ClientSession() as session:
            # 1. Upload the image + parse configuration.
            form = aiohttp.FormData()
            form.add_field(
                "file", image_data, filename=filename, content_type="application/octet-stream"
            )
            form.add_field(
                "configuration", json.dumps({"tier": tier, "version": "latest"})
            )
            async with session.post(
                f"{LLAMA_PARSE_BASE}/api/v2/parse/upload",
                headers=headers,
                data=form,
                timeout=aiohttp.ClientTimeout(total=60),
            ) as resp:
                if resp.status != 200:
                    logger.warning(
                        f"LlamaParse upload error {resp.status}: {await resp.text()}"
                    )
                    return None
                upload = await resp.json()

            job_id = upload.get("id") or upload.get("job_id")
            if not job_id:
                logger.warning("LlamaParse upload returned no job id")
                return None

            # 2. Poll until the job completes.
            status = ""
            job = {}
            for _ in range(90):
                await asyncio.sleep(2)
                async with session.get(
                    f"{LLAMA_PARSE_BASE}/api/v2/parse/{job_id}?expand=text_full",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as resp:
                    if resp.status != 200:
                        continue
                    job = await resp.json()
                status = (job.get("status") or "").upper()
                if status in ("COMPLETED", "FAILED", "CANCELLED"):
                    break

            if status != "COMPLETED":
                logger.warning(f"LlamaParse job ended with status '{status}'")
                return None

            return job.get("text_full") or _first_page_text(job)
    except Exception as e:
        logger.warning(f"LlamaParse OCR failed: {e}")
        return None


def _sniff_image_filename(image_data: bytes) -> str:
    """Return a filename based on the image's magic bytes."""
    if image_data.startswith(b"\x89PNG"):
        return "image.png"
    if image_data.startswith(b"\xff\xd8\xff"):
        return "image.jpg"
    if image_data.startswith(b"GIF8"):
        return "image.gif"
    if image_data.startswith(b"RIFF") and image_data[8:12] == b"WEBP":
        return "image.webp"
    if image_data.startswith(b"BM"):
        return "image.bmp"
    return "image.png"


def _first_page_text(job: dict) -> str | None:
    """Fall back to per-page text when `text_full` is absent."""
    pages = ((job.get("text") or {}).get("pages")) or []
    parts = [p.get("text", "") for p in pages if p.get("text")]
    return "\n".join(parts) if parts else None

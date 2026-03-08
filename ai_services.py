"""
ai_services.py — AI triage layer for telegramForward.

Each incoming Telegram message is passed to an AI model which decides:
  - Whether to forward it to Discord ("forward" | "discard")
  - An optional rewritten/summarised version of the text to send instead

The AI provider, model, and per-channel system prompts are all stored
in the PostgreSQL database (tele_settings / tele_channels).

Supported providers: openai, google, grok, deepseek, sonar, glm
"""

import os
import asyncio
import logging
import json
import aiohttp

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Default prompts (used when a channel has no custom prompt set)
# ---------------------------------------------------------------------------

DEFAULT_TRIAGE_PROMPT = """You are a financial signal triage assistant.

Your job is to evaluate an incoming message from a Telegram trading/finance channel
and decide whether it contains actionable, meaningful information worth forwarding
to a Discord community.

FORWARD the message if it contains:
- Trading signals (buy/sell calls, entry/exit levels, stop-loss, take-profit)
- Market analysis or commentary (technical or fundamental)
- Important news with clear market impact
- Charts or images with meaningful context

DISCARD the message if it contains:
- Greetings, filler, or promotional text ("Good morning!", "Join our VIP!", etc.)
- Generic motivational content with no market information
- Spam, repetitive content, or advertisements
- Off-topic conversation

Respond with valid JSON only. No markdown, no extra text.
Format:
{
  "action": "forward" | "discard",
  "reason": "<one short sentence explaining why>"
}
"""

DEFAULT_FORMAT_PROMPT = """You are a financial content formatter for a Discord community.

You will receive a Telegram message that has already been approved for forwarding.
Your job is to rewrite it into clean, well-structured Discord markdown.

Rules:
- Preserve all factual content — never remove or alter numbers, tickers, or signals
- Use **bold** for key figures, tickers, and action words (BUY, SELL, TP, SL)
- Use bullet points for multi-part information
- Remove noise: excessive emojis, ALL-CAPS filler, promotional language
- Keep it concise — trim fluff without losing substance
- If the message is already clean and concise, return it unchanged

Respond with the formatted message text only. No JSON, no commentary.
"""

# ---------------------------------------------------------------------------
# Low-level provider queries
# ---------------------------------------------------------------------------

async def _query_openai(session: aiohttp.ClientSession, prompt: str, system: str, model: str, api_key: str) -> str:
    url = "https://api.openai.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    
    # gpt-5-nano only supports temperature=1.0
    temperature = 1.0 if "gpt-5" in model.lower() or "nano" in model.lower() else 0.1
    
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user",   "content": prompt},
        ],
        "temperature": temperature,
    }
    async with session.post(url, headers=headers, json=payload, timeout=aiohttp.ClientTimeout(total=30)) as resp:
        if resp.status == 200:
            return (await resp.json())["choices"][0]["message"]["content"]
        raise Exception(f"OpenAI error {resp.status}: {await resp.text()}")


async def _query_google(session: aiohttp.ClientSession, prompt: str, system: str, model: str, api_key: str) -> str:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "system_instruction": {"parts": [{"text": system}]},
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.1},
    }
    async with session.post(url, headers=headers, json=payload, timeout=aiohttp.ClientTimeout(total=30)) as resp:
        if resp.status == 200:
            return (await resp.json())["candidates"][0]["content"]["parts"][0]["text"]
        raise Exception(f"Google error {resp.status}: {await resp.text()}")


async def _query_grok(session: aiohttp.ClientSession, prompt: str, system: str, model: str, api_key: str) -> str:
    url = "https://api.x.ai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user",   "content": prompt},
        ],
        "temperature": 0.1,
    }
    async with session.post(url, headers=headers, json=payload, timeout=aiohttp.ClientTimeout(total=30)) as resp:
        if resp.status == 200:
            return (await resp.json())["choices"][0]["message"]["content"]
        raise Exception(f"Grok error {resp.status}: {await resp.text()}")


async def _query_deepseek(session: aiohttp.ClientSession, prompt: str, system: str, model: str, api_key: str) -> str:
    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user",   "content": prompt},
        ],
        "temperature": 0.1,
    }
    async with session.post(url, headers=headers, json=payload, timeout=aiohttp.ClientTimeout(total=30)) as resp:
        if resp.status == 200:
            return (await resp.json())["choices"][0]["message"]["content"]
        raise Exception(f"DeepSeek error {resp.status}: {await resp.text()}")


async def _query_sonar(session: aiohttp.ClientSession, prompt: str, system: str, model: str, api_key: str) -> str:
    """Perplexity SONAR API — same endpoint as the old perplexity provider."""
    url = "https://api.perplexity.ai/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user",   "content": prompt},
        ],
        "temperature": 0.1,
    }
    async with session.post(url, headers=headers, json=payload, timeout=aiohttp.ClientTimeout(total=30)) as resp:
        if resp.status == 200:
            return (await resp.json())["choices"][0]["message"]["content"]
        raise Exception(f"Sonar error {resp.status}: {await resp.text()}")


async def _query_glm(session: aiohttp.ClientSession, prompt: str, system: str, model: str, api_key: str) -> str:
    """Zhipu AI GLM via the official zai-sdk (async, overseas endpoint).

    Uses thinking mode (chain-of-thought) when the model supports it.
    temperature must be 1.0 when thinking is enabled (Z.ai requirement).
    The final JSON answer lives in message.content; reasoning_content is ignored.
    """
    from zai import ZaiClient

    client = ZaiClient(api_key=api_key)

    # zai-sdk is synchronous — run in a thread pool to avoid blocking the event loop
    def _sync_call():
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": prompt},
            ],
            thinking={"type": "enabled"},
            temperature=1.0,   # required by Z.ai when thinking is enabled
            max_tokens=4096,
        )
        return resp.choices[0].message.content

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _sync_call)


# ---------------------------------------------------------------------------
# Provider router
# ---------------------------------------------------------------------------

async def _call_provider(session: aiohttp.ClientSession, prompt: str, system: str,
                         provider: str, model: str, api_key: str) -> str:
    if provider == "openai":
        return await _query_openai(session, prompt, system, model, api_key)
    elif provider == "google":
        return await _query_google(session, prompt, system, model, api_key)
    elif provider == "grok":
        return await _query_grok(session, prompt, system, model, api_key)
    elif provider == "deepseek":
        return await _query_deepseek(session, prompt, system, model, api_key)
    elif provider in ("sonar", "perplexity"):   # perplexity kept as legacy alias
        return await _query_sonar(session, prompt, system, model, api_key)
    elif provider == "glm":
        return await _query_glm(session, prompt, system, model, api_key)
    else:
        raise ValueError(f"Unknown AI provider: '{provider}'")


# ---------------------------------------------------------------------------
# Triage result dataclass
# ---------------------------------------------------------------------------

class TriageResult:
    def __init__(self, action: str, reason: str, rewritten_text: str | None):
        self.action         = action          # "forward" | "discard"
        self.reason         = reason
        self.rewritten_text = rewritten_text  # None means use original text

    def __repr__(self):
        return f"TriageResult(action={self.action!r}, reason={self.reason!r})"


# ---------------------------------------------------------------------------
# Public triage function
# ---------------------------------------------------------------------------

async def triage_message(
    message_text: str,
    channel_name: str,
    triage_prompt: str,
    format_prompt: str,
    provider: str,
    model: str,
    api_key: str,
) -> TriageResult:
    """
    Two-pass AI pipeline:
      Pass 1 — Triage: decide "forward" or "discard" using triage_prompt.
      Pass 2 — Format: rewrite the approved message using format_prompt.

    On any error (network, parse, etc.) the message is always forwarded
    unchanged so a failing AI never silently drops messages.
    """
    if not message_text or not message_text.strip():
        return TriageResult("forward", "empty message, skipped triage", None)

    user_prompt = f"Channel: {channel_name}\n\nMessage:\n{message_text}"

    # ── Pass 1: Triage ────────────────────────────────────────────────────
    try:
        async with aiohttp.ClientSession() as session:
            raw = await asyncio.wait_for(
                _call_provider(session, user_prompt, triage_prompt, provider, model, api_key),
                timeout=35.0,
            )

        clean = raw.strip()
        if clean.startswith("```"):
            clean = clean.split("```")[1]
            if clean.startswith("json"):
                clean = clean[4:]
            clean = clean.strip()

        data   = json.loads(clean)
        action = str(data.get("action", "forward")).lower()
        reason = str(data.get("reason", ""))

        if action not in ("forward", "discard"):
            logger.warning(f"AI triage returned unexpected action '{action}', defaulting to forward")
            action = "forward"

        logger.info(f"AI triage [{channel_name}]: {action} — {reason}")

    except asyncio.TimeoutError:
        logger.warning(f"AI triage timed out for '{channel_name}' — forwarding original")
        return TriageResult("forward", "triage timed out", None)
    except (json.JSONDecodeError, KeyError) as e:
        logger.warning(f"AI triage invalid JSON for '{channel_name}': {e} — forwarding original")
        return TriageResult("forward", f"invalid triage response: {e}", None)
    except Exception as e:
        logger.error(f"AI triage error for '{channel_name}': {e} — forwarding original")
        return TriageResult("forward", f"triage error: {e}", None)

    if action == "discard":
        return TriageResult("discard", reason, None)

    # ── Pass 2: Format ────────────────────────────────────────────────────
    rewritten: str | None = None
    try:
        async with aiohttp.ClientSession() as session:
            rewritten = await asyncio.wait_for(
                _call_provider(session, message_text, format_prompt, provider, model, api_key),
                timeout=35.0,
            )
        rewritten = rewritten.strip() or None
        logger.info(f"AI format [{channel_name}]: rewritten ({len(rewritten or '')} chars)")

    except asyncio.TimeoutError:
        logger.warning(f"AI format timed out for '{channel_name}' — using original text")
    except Exception as e:
        logger.warning(f"AI format error for '{channel_name}': {e} — using original text")

    return TriageResult("forward", reason, rewritten)

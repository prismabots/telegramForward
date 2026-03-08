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
# Default triage prompt (used when a channel has no custom ai_prompt)
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
  "reason": "<one short sentence explaining why>",
  "rewritten_text": "<optional cleaned-up version of the message — omit or null if no rewrite needed>"
}
"""

# ---------------------------------------------------------------------------
# Low-level provider queries
# ---------------------------------------------------------------------------

async def _query_openai(session: aiohttp.ClientSession, prompt: str, system: str, model: str, api_key: str) -> str:
    url = "https://api.openai.com/v1/chat/completions"
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
    """Zhipu AI GLM via the official zai-sdk (async, overseas endpoint)."""
    from zai import ZaiClient
    import asyncio

    client = ZaiClient(api_key=api_key)

    # zai-sdk is synchronous — run in a thread pool to avoid blocking the event loop
    def _sync_call():
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": prompt},
            ],
            temperature=0.1,
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
    system_prompt: str,
    provider: str,
    model: str,
    api_key: str,
) -> TriageResult:
    """
    Run the message through the configured AI model and return a TriageResult.

    On any error (network, parse, etc.) the message is always forwarded
    unchanged so a failing AI never silently drops messages.
    """
    if not message_text or not message_text.strip():
        # Nothing to triage — forward as-is
        return TriageResult("forward", "empty message, skipped triage", None)

    user_prompt = f"Channel: {channel_name}\n\nMessage:\n{message_text}"

    try:
        async with aiohttp.ClientSession() as session:
            raw = await asyncio.wait_for(
                _call_provider(session, user_prompt, system_prompt, provider, model, api_key),
                timeout=35.0,
            )

        # Strip markdown code fences if the model wraps its JSON
        clean = raw.strip()
        if clean.startswith("```"):
            clean = clean.split("```")[1]
            if clean.startswith("json"):
                clean = clean[4:]
            clean = clean.strip()

        data = json.loads(clean)
        action   = str(data.get("action", "forward")).lower()
        reason   = str(data.get("reason", ""))
        rewrite  = data.get("rewritten_text") or None

        if action not in ("forward", "discard"):
            logger.warning(f"AI returned unexpected action '{action}', defaulting to forward")
            action = "forward"

        logger.info(f"AI triage [{channel_name}]: {action} — {reason}")
        return TriageResult(action, reason, rewrite)

    except asyncio.TimeoutError:
        logger.warning(f"AI triage timed out for channel '{channel_name}' — forwarding original")
        return TriageResult("forward", "triage timed out", None)
    except (json.JSONDecodeError, KeyError) as e:
        logger.warning(f"AI triage returned invalid JSON for '{channel_name}': {e} — forwarding original")
        return TriageResult("forward", f"invalid AI response: {e}", None)
    except Exception as e:
        logger.error(f"AI triage error for '{channel_name}': {e} — forwarding original")
        return TriageResult("forward", f"triage error: {e}", None)

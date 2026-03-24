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

# Channel IDs and names for detailed logging
SPX_CHANNEL_ID = 13
KYLE_TEST_CHANNEL_ID = 16

def _is_spx_channel(channel_id: int | None, channel_name: str) -> bool:
    """Check if this is the SPX Options AI channel or KyleTestgroup (test channel)."""
    return (channel_id == SPX_CHANNEL_ID or channel_id == KYLE_TEST_CHANNEL_ID or 
            "SPX" in channel_name or "Kyle" in channel_name)

def _log_spx_input(channel_id: int | None, channel_name: str, message_text: str, 
                   triage_prompt: str, provider: str, model: str) -> None:
    """Log SPX channel input for debugging."""
    if not _is_spx_channel(channel_id, channel_name):
        return
    logger.info(f"\n{'='*80}")
    logger.info(f"[SPX AI INPUT] Channel: {channel_name} (ID {channel_id})")
    logger.info(f"[SPX AI INPUT] Provider: {provider} | Model: {model}")
    logger.info(f"[SPX AI INPUT] Message ({len(message_text)} chars):")
    logger.info(f"  {repr(message_text[:200])}")
    if len(message_text) > 200:
        logger.info(f"  ... ({len(message_text) - 200} more chars)")
    logger.info(f"[SPX AI INPUT] Triage Prompt ({len(triage_prompt)} chars):")
    logger.info(f"  {repr(triage_prompt[:150])}")
    if len(triage_prompt) > 150:
        logger.info(f"  ... ({len(triage_prompt) - 150} more chars)")
    logger.info(f"{'='*80}\n")

def _log_spx_triage_output(channel_id: int | None, channel_name: str, action: str, 
                           reason: str, raw_response: str | None = None) -> None:
    """Log SPX channel triage output."""
    if not _is_spx_channel(channel_id, channel_name):
        return
    logger.info(f"\n{'='*80}")
    logger.info(f"[SPX AI TRIAGE OUTPUT] Channel: {channel_name} (ID {channel_id})")
    logger.info(f"[SPX AI TRIAGE OUTPUT] Action: {action}")
    logger.info(f"[SPX AI TRIAGE OUTPUT] Reason: {reason}")
    if raw_response:
        logger.info(f"[SPX AI TRIAGE OUTPUT] Raw Response ({len(raw_response)} chars):")
        logger.info(f"  {repr(raw_response[:300])}")
        if len(raw_response) > 300:
            logger.info(f"  ... ({len(raw_response) - 300} more chars)")
    logger.info(f"{'='*80}\n")

def _log_spx_format_output(channel_id: int | None, channel_name: str, 
                          original_text: str, formatted_text: str | None) -> None:
    """Log SPX channel format output."""
    if not _is_spx_channel(channel_id, channel_name):
        return
    logger.info(f"\n{'='*80}")
    logger.info(f"[SPX AI FORMAT OUTPUT] Channel: {channel_name} (ID {channel_id})")
    logger.info(f"[SPX AI FORMAT OUTPUT] Original Text ({len(original_text)} chars):")
    logger.info(f"  {repr(original_text[:250])}")
    if len(original_text) > 250:
        logger.info(f"  ... ({len(original_text) - 250} more chars)")
    if formatted_text:
        logger.info(f"[SPX AI FORMAT OUTPUT] Formatted Text ({len(formatted_text)} chars):")
        logger.info(f"  {repr(formatted_text[:250])}")
        if len(formatted_text) > 250:
            logger.info(f"  ... ({len(formatted_text) - 250} more chars)")
    else:
        logger.info(f"[SPX AI FORMAT OUTPUT] Formatted Text: None (using original)")
    logger.info(f"{'='*80}\n")

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
    logger.debug(f"Querying Grok: model={model}, prompt_len={len(prompt)}, api_key={api_key[:20]}...")
    async with session.post(url, headers=headers, json=payload, timeout=aiohttp.ClientTimeout(total=30)) as resp:
        if resp.status == 200:
            result = (await resp.json())["choices"][0]["message"]["content"]
            logger.debug(f"Grok success: {len(result)} chars returned")
            return result
        error_text = await resp.text()
        logger.error(f"Grok error {resp.status}: {error_text[:500]}")
        raise Exception(f"Grok error {resp.status}: {error_text}")


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
    is_reply: bool = False,
    parent_message_text: str | None = None,
    channel_id: int | None = None,
    verbose_logging: bool = True,
    fallback_provider: str | None = None,
    fallback_model: str | None = None,
    fallback_api_key: str | None = None,
) -> TriageResult:
    """
    Two-pass AI pipeline with automatic fallback:
      Pass 1 — Triage: decide "forward" or "discard" using triage_prompt.
      Pass 2 — Format: rewrite the approved message using format_prompt.

    If the primary provider fails, automatically retries with the fallback provider.
    On any error after retries, the message is forwarded unchanged so a failing AI 
    never silently drops messages.
    
    Args:
        is_reply: If True, indicates this is a reply/update to a previous message
        parent_message_text: Text of the parent message (if this is a reply)
        fallback_provider: Secondary AI provider to use if primary fails
        fallback_model: Model to use with fallback provider
        fallback_api_key: API key for fallback provider
    """
    if not message_text or not message_text.strip():
        return TriageResult("forward", "empty message, skipped triage", None)

    # Build context for replies with parent message
    reply_context = ""
    if is_reply:
        reply_context = "\n[NOTE: This is a REPLY/UPDATE to a previous message]"
        if parent_message_text and parent_message_text.strip():
            reply_context += f"\n[PARENT MESSAGE]:\n{parent_message_text}\n[END PARENT MESSAGE]"
    
    user_prompt = f"Channel: {channel_name}{reply_context}\n\nMessage:\n{message_text}"
    
    # Log SPX AI input
    _log_spx_input(channel_id, channel_name, message_text, triage_prompt, provider, model)

    # ── Pass 1: Triage ────────────────────────────────────────────────────
    triage_error = None
    try:
        if verbose_logging:
            logger.info(f"[{channel_name}] Starting triage with {provider}/{model}")
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

        if verbose_logging:
            logger.info(f"AI triage [{channel_name}]: {action} — {reason}")
        
        # Log SPX triage output
        _log_spx_triage_output(channel_id, channel_name, action, reason, raw)

    except asyncio.TimeoutError as e:
        triage_error = f"timeout ({provider})"
        logger.warning(f"AI triage TIMEOUT (35s) for '{channel_name}' [{provider}] - {type(e).__name__}: {e}")
        logger.info(f"[{channel_name}] Attempting fallback due to timeout...")
    except (json.JSONDecodeError, KeyError) as e:
        triage_error = f"invalid JSON ({provider}): {e}"
        logger.warning(f"AI triage invalid JSON for '{channel_name}' [{provider}]: {e} — attempting fallback")
    except Exception as e:
        triage_error = f"error ({provider}): {e}"
        logger.error(f"AI triage ERROR for '{channel_name}' [{provider}] - {type(e).__name__}: {str(e)[:200]}")
        logger.info(f"[{channel_name}] Attempting fallback due to error...")

    # Try fallback if primary failed AND we have a fallback configured
    if triage_error:
        if not fallback_provider:
            logger.warning(f"AI triage failed and no fallback_provider configured for '{channel_name}' — forwarding original")
            return TriageResult("forward", f"triage error: {triage_error}", None)
        if not fallback_model:
            logger.warning(f"AI triage failed and no fallback_model configured for '{channel_name}' — forwarding original")
            return TriageResult("forward", f"triage error: {triage_error}", None)
        if not fallback_api_key:
            logger.warning(f"AI triage failed and fallback API key not available for '{channel_name}' ({fallback_provider}) — forwarding original")
            return TriageResult("forward", f"triage error: {triage_error}; fallback API key missing", None)
        
        logger.info(f"[{channel_name}] Falling back to {fallback_provider}/{fallback_model} for triage (reason: {triage_error})")
        try:
            async with aiohttp.ClientSession() as session:
                raw = await asyncio.wait_for(
                    _call_provider(session, user_prompt, triage_prompt, fallback_provider, fallback_model, fallback_api_key),
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
                logger.warning(f"AI triage (fallback) returned unexpected action '{action}', defaulting to forward")
                action = "forward"

            if verbose_logging:
                logger.info(f"AI triage [{channel_name}] (FALLBACK {fallback_provider}): {action} — {reason}")
            
            # Log SPX triage output (fallback)
            _log_spx_triage_output(channel_id, channel_name, action, reason, raw)
            triage_error = None  # Clear error since fallback succeeded

        except asyncio.TimeoutError:
            logger.warning(f"AI triage fallback also timed out for '{channel_name}' [{fallback_provider}] — forwarding original")
            return TriageResult("forward", f"triage failed: {triage_error}; fallback timed out", None)
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"AI triage fallback invalid JSON for '{channel_name}' [{fallback_provider}]: {e} — forwarding original")
            return TriageResult("forward", f"triage failed: {triage_error}; fallback parse error: {e}", None)
        except Exception as e:
            logger.error(f"AI triage fallback error for '{channel_name}' [{fallback_provider}]: {e} — forwarding original")
            return TriageResult("forward", f"triage failed: {triage_error}; fallback error: {e}", None)
    elif triage_error:
        # Primary failed but no fallback available
        logger.warning(f"AI triage failed and no fallback configured for '{channel_name}' — forwarding original")
        return TriageResult("forward", f"triage error: {triage_error}", None)

    if action == "discard":
        # Log SPX discard decision
        _log_spx_triage_output(channel_id, channel_name, "discard", reason)
        return TriageResult("discard", reason, None)

    # ── Pass 2: Format ────────────────────────────────────────────────────
    rewritten: str | None = None
    format_error = None
    try:
        if verbose_logging:
            logger.info(f"[{channel_name}] Starting format with {provider}/{model}")
        async with aiohttp.ClientSession() as session:
            rewritten = await asyncio.wait_for(
                _call_provider(session, message_text, format_prompt, provider, model, api_key),
                timeout=60.0,  # Increased for long messages with many trades
            )
        rewritten = rewritten.strip() or None
        if verbose_logging:
            logger.info(f"AI format [{channel_name}]: rewritten ({len(rewritten or '')} chars)")

    except asyncio.TimeoutError as e:
        format_error = f"timeout ({provider})"
        logger.warning(f"AI format TIMEOUT (60s) for '{channel_name}' [{provider}]")
    except Exception as e:
        format_error = f"error ({provider}): {e}"
        logger.error(f"AI format ERROR for '{channel_name}' [{provider}] - {type(e).__name__}: {str(e)[:200]}")

    # Try fallback for format if primary failed AND we have a fallback configured
    if format_error:
        if fallback_provider and fallback_model and fallback_api_key:
            logger.info(f"[{channel_name}] Falling back to {fallback_provider}/{fallback_model} for format (reason: {format_error})")
            try:
                async with aiohttp.ClientSession() as session:
                    rewritten = await asyncio.wait_for(
                        _call_provider(session, message_text, format_prompt, fallback_provider, fallback_model, fallback_api_key),
                        timeout=60.0,
                    )
                rewritten = rewritten.strip() or None
                if verbose_logging:
                    logger.info(f"AI format [{channel_name}] (FALLBACK {fallback_provider}): rewritten ({len(rewritten or '')} chars)")
                format_error = None  # Clear error since fallback succeeded

            except asyncio.TimeoutError:
                logger.warning(f"AI format fallback also timed out for '{channel_name}' [{fallback_provider}] — using original text")
            except Exception as e:
                logger.warning(f"AI format fallback error for '{channel_name}' [{fallback_provider}]: {e} — using original text")
        else:
            # Primary format failed but no fallback available - just use original text
            missing = []
            if not fallback_provider:
                missing.append("provider")
            if not fallback_model:
                missing.append("model")
            if not fallback_api_key:
                missing.append("api_key")
            logger.warning(f"AI format failed and fallback not fully configured for '{channel_name}' (missing: {', '.join(missing)}) — using original text")

    # Log SPX format output
    _log_spx_format_output(channel_id, channel_name, message_text, rewritten)
    
    return TriageResult("forward", reason, rewritten)

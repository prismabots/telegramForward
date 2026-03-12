from telethon import TelegramClient, events
from telethon.tl.functions.messages import CheckChatInviteRequest
from telethon.tl.types import MessageMediaWebPage, WebPage
import requests
import logging
from datetime import datetime
import os
import tempfile
import mimetypes
import json
import discord_embeds
import sys

# Ensure db module is importable from the same directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import db
from ai_services import triage_message, DEFAULT_TRIAGE_PROMPT, DEFAULT_FORMAT_PROMPT

# ---------------------------------------------------------------------------
# Logging setup (basic level first; overridden after DB load below)
# ---------------------------------------------------------------------------
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Verbose logging control - only these channels get detailed logs
# ---------------------------------------------------------------------------
VERBOSE_CHANNELS = [13, 14]  # Control Optional SPX, Algo Pro

def should_log_verbose(channel_id: int) -> bool:
    """Check if this channel should have verbose logging."""
    return channel_id in VERBOSE_CHANNELS

# ---------------------------------------------------------------------------
# Database init + load all config
# ---------------------------------------------------------------------------

if not os.environ.get("BACKUP_DB_ADMIN_URL"):
    logger.error("BACKUP_DB_ADMIN_URL environment variable is not set.")
    sys.exit(1)

logger.info("Connecting to database and initialising schema...")
db.init_db()

settings = db.get_all_settings()

# Apply log level from DB
log_level = settings.get("log_level", "INFO").upper()
logging.getLogger().setLevel(getattr(logging, log_level, logging.INFO))

# Telegram credentials (all from DB)
api_id_str   = settings.get("telegram_api_id")
api_hash     = settings.get("telegram_api_hash")
session_name = settings.get("telegram_session_name", "anon")

if not api_id_str or not api_hash:
    logger.error(
        "telegram_api_id and telegram_api_hash must be set in the DB settings table.\n"
        "Run: python cli.py setting set telegram_api_id <your_id>"
    )
    sys.exit(1)

api_id = int(api_id_str)

# Bot display name for Discord
bot_username = settings.get("bot_username", "Telegram Forward Bot")

# ---------------------------------------------------------------------------
# AI triage config (loaded from DB settings)
# ---------------------------------------------------------------------------

ai_provider = settings.get("ai_provider", "openai")

# Per-provider default models (used when ai_model is not set in DB)
_AI_DEFAULT_MODELS = {
    "openai":   "gpt-5-nano",
    "google":   "gemini-2.0-flash",
    "grok":     "grok-4.1-fast",
    "deepseek": "deepseek-chat",
    "sonar":    "sonar",
    "glm":      "glm-4.7-flashx",
}
ai_model = settings.get("ai_model") or _AI_DEFAULT_MODELS.get(ai_provider, "gpt-5-nano")

# API keys are stored as DigitalOcean environment variables — one per provider.
# The DB setting ai_api_key (if set) still takes precedence for local overrides.
_AI_KEY_ENV_MAP = {
    "openai":     "OPENAI_API_KEY",
    "google":     "GOOGLE_API_KEY",
    "grok":       "X_API_KEY",
    "deepseek":   "DEEPSEEK_API_KEY",
    "sonar":      "SONAR_API_KEY",
    "glm":        "GLM_API_KEY",
}
ai_api_key = (
    settings.get("ai_api_key", "")
    or os.environ.get(_AI_KEY_ENV_MAP.get(ai_provider, ""), "")
)


# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# Discord channel ID fetcher
# ---------------------------------------------------------------------------

def fetch_discord_channel_id(webhook_url: str) -> str | None:
    """
    Query the Discord webhook info endpoint to get the channel_id.
    This is required for message_reference (reply threading) to work.
    Returns the channel_id string, or None on failure.
    """
    try:
        # Strip query string before hitting the info endpoint
        base_url = webhook_url.split("?")[0]
        resp = requests.get(base_url, timeout=10)
        resp.raise_for_status()
        channel_id = str(resp.json().get("channel_id", ""))
        if channel_id:
            logger.info(f"Discord channel_id for webhook: {channel_id}")
        return channel_id or None
    except Exception as e:
        logger.warning(f"Could not fetch Discord channel_id from webhook: {e}")
        return None


def fetch_discord_guild_id(webhook_url: str) -> str | None:
    """
    Query the Discord webhook info endpoint to get the guild_id.
    This is required for building Discord message links.
    Returns the guild_id string, or None on failure.
    """
    try:
        # Strip query string before hitting the info endpoint
        base_url = webhook_url.split("?")[0]
        resp = requests.get(base_url, timeout=10)
        resp.raise_for_status()
        guild_id = str(resp.json().get("guild_id", ""))
        if guild_id:
            logger.info(f"Discord guild_id for webhook: {guild_id}")
        return guild_id or None
    except Exception as e:
        logger.warning(f"Could not fetch Discord guild_id from webhook: {e}")
        return None



# ---------------------------------------------------------------------------
# Load channels from DB
# ---------------------------------------------------------------------------

db_channels = db.get_channels(enabled_only=True)

if not db_channels:
    logger.error(
        "No enabled channels found in the database.\n"
        "Run: python cli.py channel add --name '...' --chat-id '...' --webhook 'https://...'"
    )
    sys.exit(1)

# channel_configs: chat_id (username) -> {webhook, name, db_id}
# Populated from DB; used during resolve phase.
channel_configs: dict[str, dict] = {}
logger.info(f"Loading {len(db_channels)} channels from database...")
for ch in db_channels:
    webhook_url = ch["discord_webhook"]
    channel_name = ch["name"]
    
    logger.info(f"Fetching Discord IDs for '{channel_name}'...")
    discord_channel_id = fetch_discord_channel_id(webhook_url)
    discord_guild_id = fetch_discord_guild_id(webhook_url)
    
    if not discord_channel_id:
        logger.error(f"❌ Failed to fetch discord_channel_id for '{channel_name}'")
    if not discord_guild_id:
        logger.error(f"❌ Failed to fetch discord_guild_id for '{channel_name}'")
    
    logger.info(
        f"✓ '{channel_name}': channel_id={discord_channel_id}, guild_id={discord_guild_id}"
    )
    
    channel_configs[ch["chat_id"]] = {
        "webhook":            webhook_url,
        "name":               channel_name,
        "db_id":              ch["id"],
        "role_id":            ch.get("discord_role_id"),
        "discord_channel_id": discord_channel_id,
        "discord_guild_id":   discord_guild_id,
        "ai_enabled":         ch.get("ai_enabled", False),
        "ai_triage_prompt":   ch.get("ai_triage_prompt") or DEFAULT_TRIAGE_PROMPT,
        "ai_format_prompt":   ch.get("ai_format_prompt") or DEFAULT_FORMAT_PROMPT,
        "ai_provider":        ch.get("ai_provider"),  # Per-channel AI provider override
        "ai_model":           ch.get("ai_model"),     # Per-channel AI model override
    }

# channel_webhook_map: numeric Telegram channel ID -> {webhook, name, db_id}
# Populated after Telethon resolves entities.
channel_webhook_map: dict[int, dict] = {}

# ---------------------------------------------------------------------------
# Telegram client
# ---------------------------------------------------------------------------
client = TelegramClient(session_name, api_id, api_hash)


# ---------------------------------------------------------------------------
# Media helpers
# ---------------------------------------------------------------------------

def is_video(file_path: str) -> bool:
    mime_type, _ = mimetypes.guess_type(file_path)
    return bool(mime_type and mime_type.startswith("video"))


def is_image(file_path: str) -> bool:
    mime_type, _ = mimetypes.guess_type(file_path)
    return bool(mime_type and mime_type.startswith("image"))


def get_file_extension(file_path: str) -> str:
    _, ext = os.path.splitext(file_path)
    return ext if ext else ""


def detect_media_type(file_path: str) -> str | None:
    """Return 'photo', 'video', or 'document' for a local file path."""
    if is_image(file_path):
        return "photo"
    if is_video(file_path):
        return "video"
    return "document"


# ---------------------------------------------------------------------------
# Discord sending
# ---------------------------------------------------------------------------

async def send_to_discord(
    webhook_url: str,
    message_text: str,
    media_path: str | None = None,
    reply_to_discord_id: str | None = None,
    role_id: str | None = None,
    discord_channel_id: str | None = None,
    discord_guild_id: str | None = None,
    quoted_text: str | None = None,
    channel_id: int | None = None,
) -> tuple[str | None, str | None]:
    """
    Send a message (and optional media) to a Discord webhook.

    Uses ?wait=true so Discord returns the created message object,
    allowing us to capture the discord_message_id for reply threading.

    If role_id is provided, a role mention is prepended to the message.
    discord_channel_id and discord_guild_id are required for building reply links.
    quoted_text is the text from the original message being replied to.

    Returns:
        (discord_message_id, actual_text_sent) or (None, None) on failure.
    """
    # Append ?wait=true to get response body with message id
    url = webhook_url.rstrip("/") + ("&" if "?" in webhook_url else "?") + "wait=true"

    # Build reply link if applicable
    reply_link = None
    if reply_to_discord_id and discord_channel_id and discord_guild_id:
        reply_link = f"https://discord.com/channels/{discord_guild_id}/{discord_channel_id}/{reply_to_discord_id}"
    elif reply_to_discord_id and (not discord_channel_id or not discord_guild_id):
        logger.warning(
            f"Cannot create reply link to Discord message {reply_to_discord_id}: "
            f"discord_channel_id={discord_channel_id!r}, discord_guild_id={discord_guild_id!r}"
        )

    try:
        if media_path:
            # Media with embed
            mime_type, _ = mimetypes.guess_type(media_path)
            ext = get_file_extension(media_path)

            if is_image(media_path):
                filename     = f"image{ext or '.png'}"
                content_type = mime_type or "image/png"
            elif is_video(media_path):
                filename     = f"video{ext or '.mp4'}"
                content_type = mime_type or "video/mp4"
            else:
                filename     = f"file{ext}"
                content_type = mime_type or "application/octet-stream"

            # Build embed for media message (use message_text or empty string)
            text_to_send = message_text if message_text else ""
            payload = discord_embeds.create_webhook_payload(
                message_text=text_to_send,
                role_id=role_id,
                quoted_text=quoted_text,
                username=bot_username,
                use_embed=True,
                channel_id=channel_id,
                verbose_logging=(channel_id is not None and should_log_verbose(channel_id)),
            )
            
            # Add reply link to embed if available
            if reply_link and payload.get('embeds'):
                payload['embeds'][0]['description'] = f"↩️ [Reply to message]({reply_link})\n\n" + payload['embeds'][0].get('description', '')

            with open(media_path, "rb") as f:
                files = {"file": (filename, f, content_type)}
                response = requests.post(
                    url,
                    data={"payload_json": json.dumps(payload)},
                    files=files,
                )
        else:
            if not message_text:
                return None, None
            
            # Build embed payload
            payload = discord_embeds.create_webhook_payload(
                message_text=message_text,
                role_id=role_id,
                quoted_text=quoted_text,
                username=bot_username,
                use_embed=True,
                channel_id=channel_id,
                verbose_logging=(channel_id is not None and should_log_verbose(channel_id)),
            )
            
            # Add reply link to embed if available
            if reply_link and payload.get('embeds'):
                embed_desc = payload['embeds'][0].get('description', '')
                reply_text = f"↩️ [Reply to message]({reply_link})"
                if embed_desc:
                    payload['embeds'][0]['description'] = f"{reply_text}\n\n{embed_desc}"
                else:
                    payload['embeds'][0]['description'] = reply_text
            
            # Debug: Log the payload
            if channel_id is not None and should_log_verbose(channel_id):
                logger.info(f"Discord payload: {json.dumps(payload, indent=2)}")
            
            response = requests.post(url, json=payload)
            
            # Debug: Log the response
            if channel_id is not None and should_log_verbose(channel_id):
                logger.info(f"Discord response status: {response.status_code}")
            if response.status_code != 200:
                logger.error(f"Discord error response: {response.text}")

        response.raise_for_status()
        resp_json          = response.json()
        discord_message_id = str(resp_json.get("id", ""))
        if channel_id is not None and should_log_verbose(channel_id):
            logger.info(f"Sent to Discord — discord_message_id={discord_message_id}")
        
        # Return the original text for logging
        return discord_message_id or None, message_text

    except Exception as e:
        # Log additional context for debugging Discord 400/Bad Request errors.
        try:
            if 'url' in locals() and isinstance(url, str) and '/webhooks/' in url:
                masked_webhook = url.split('/webhooks/')[0] + '/webhooks/...'
            else:
                masked_webhook = '(<webhook masked>)'
        except Exception:
            masked_webhook = '(<webhook masked>)'

        try:
            payload_preview = json.dumps(payload)[:1000] if 'payload' in locals() else None
        except Exception:
            payload_preview = '<could not serialize payload>'

        logger.error(
            f"Failed to send message to Discord: {e}. Webhook: {masked_webhook}. "
            f"Payload preview: {payload_preview}",
            exc_info=True,
        )
        return None, None
    finally:
        if media_path and os.path.exists(media_path):
            try:
                os.remove(media_path)
            except Exception as e:
                logger.error(f"Failed to clean up media file: {e}")


# ---------------------------------------------------------------------------
# Channel resolution
# ---------------------------------------------------------------------------

async def resolve_channels():
    """
    Resolve each configured channel and populate channel_webhook_map
    (keyed by numeric Telegram channel ID).

    Also back-fills telegram_channel_id in the DB for newly resolved
    channels.
    """
    await client.start()
    resolved = []

    for chat_id, cfg in channel_configs.items():
        try:
            if chat_id.startswith("+"):
                # Private invite link — resolve via CheckChatInvite
                invite_hash = chat_id[1:]
                result = await client(CheckChatInviteRequest(invite_hash))
                if hasattr(result, "chat"):
                    entity = result.chat
                else:
                    logger.error(
                        f"Invite link for '{cfg['name']}' not yet joined. "
                        "Join first, then restart."
                    )
                    continue
            elif chat_id.lstrip("-").isdigit():
                # Numeric channel ID (e.g. -1001916798610)
                entity = await client.get_entity(int(chat_id))
            else:
                # Public username
                entity = await client.get_entity(f"https://t.me/{chat_id}")

            numeric_id = entity.id
            channel_webhook_map[numeric_id] = {
                "webhook":            cfg["webhook"],
                "name":               cfg["name"],
                "db_id":              cfg["db_id"],
                "role_id":            cfg["role_id"],
                "discord_channel_id": cfg["discord_channel_id"],
                "discord_guild_id":   cfg["discord_guild_id"],
                "ai_enabled":         cfg["ai_enabled"],
                "ai_triage_prompt":   cfg["ai_triage_prompt"],
                "ai_format_prompt":   cfg["ai_format_prompt"],
                "ai_provider":        cfg["ai_provider"],
                "ai_model":           cfg["ai_model"],
            }
            logger.info(
                f"Resolved channel: {cfg['name']} ({chat_id}) → ID {numeric_id}"
            )

            # Back-fill numeric ID to DB if not already stored
            db.update_channel(cfg["db_id"], telegram_channel_id=numeric_id)

            resolved.append(entity)

        except Exception as e:
            logger.error(
                f"Failed to resolve channel '{cfg['name']}' ({chat_id}): {e}"
            )

    return resolved


# ---------------------------------------------------------------------------
# Media download
# ---------------------------------------------------------------------------

async def download_media_to_temp(message) -> str | None:
    try:
        if message.media:
            temp_dir  = tempfile.gettempdir()
            temp_path = os.path.join(
                temp_dir,
                f'tgfwd_{datetime.now().strftime("%Y%m%d_%H%M%S_%f")}',
            )
            path = await message.download_media(temp_path)
            logger.info(f"Media downloaded to {path}")
            return path
    except Exception as e:
        logger.error(f"Failed to download media: {e}")
    return None


# ---------------------------------------------------------------------------
# Event handler
# ---------------------------------------------------------------------------

async def handle_new_message(event):
    try:
        chat = await event.get_chat()
        if not chat or not hasattr(chat, "id"):
            return

        cfg = channel_webhook_map.get(chat.id)
        if not cfg:
            logger.warning(f"No webhook found for chat {chat.id}")
            return

        webhook_url         = cfg["webhook"]
        channel_name        = cfg["name"]
        db_channel_id       = cfg["db_id"]
        role_id             = cfg.get("role_id")
        discord_channel_id  = cfg.get("discord_channel_id")
        discord_guild_id    = cfg.get("discord_guild_id")
        ai_enabled          = cfg.get("ai_enabled", False)
        ai_triage_prompt    = cfg.get("ai_triage_prompt", DEFAULT_TRIAGE_PROMPT)
        ai_format_prompt    = cfg.get("ai_format_prompt", DEFAULT_FORMAT_PROMPT)
        
        # Per-channel AI settings (use channel-specific if set, otherwise fall back to global)
        channel_ai_provider = cfg.get("ai_provider")
        channel_ai_model    = cfg.get("ai_model")
        use_provider = channel_ai_provider if channel_ai_provider else ai_provider
        use_model    = channel_ai_model if channel_ai_model else ai_model

        if not discord_channel_id or not discord_guild_id:
            logger.warning(
                f"[{channel_name}] discord_channel_id or discord_guild_id not available — reply threading will not work"
            )

        msg          = event.message
        message_text = msg.text or msg.message or ""
        tg_msg_id    = msg.id
        tg_reply_to  = getattr(msg.reply_to, "reply_to_msg_id", None) if msg.reply_to else None
        
        # If this is a reply, fetch the original message to strip quoted text
        quoted_text = None
        if tg_reply_to is not None:
            try:
                replied_msg = await event.get_reply_message()
                if replied_msg:
                    quoted_text = replied_msg.text or replied_msg.message or ""
                    # Strip the quoted text from the beginning of the message if present
                    if quoted_text and message_text.startswith(quoted_text):
                        message_text = message_text[len(quoted_text):].strip()
                        if should_log_verbose(db_channel_id):
                            logger.info(f"[{channel_name}] Stripped quoted text from reply ({len(quoted_text)} chars)")
            except Exception as e:
                logger.warning(f"[{channel_name}] Could not fetch reply message: {e}")

        # If the message has no text but has a WebPage media (link preview),
        # extract the URL so we don't silently drop link-only messages.
        if not message_text and msg.media:
            try:
                if isinstance(msg.media, MessageMediaWebPage) and isinstance(msg.media.webpage, WebPage):
                    message_text = msg.media.webpage.url or ""
            except Exception:
                pass

        # Sender info
        sender = await event.get_sender()
        sender_id   = sender.id if sender else None
        sender_name = (
            getattr(sender, "username", None)
            or getattr(sender, "first_name", None)
            or str(sender_id)
            if sender else None
        )

        # Media
        media_path      = None
        media_type      = None
        media_file_name = None
        if msg.media:
            media_path      = await download_media_to_temp(msg)
            if media_path:
                media_type      = detect_media_type(media_path)
                media_file_name = os.path.basename(media_path)

        # Reply threading — look up corresponding Discord message
        reply_to_discord_id = None
        if tg_reply_to is not None:
            logger.debug(
                f"[{channel_name}] Message {tg_msg_id} is a reply to Telegram message {tg_reply_to}"
            )
            reply_to_discord_id = db.get_discord_msg_id(db_channel_id, tg_reply_to)
            if reply_to_discord_id:
                logger.debug(
                    f"[{channel_name}] Threading: TG {tg_reply_to} → Discord {reply_to_discord_id}"
                )
            else:
                logger.warning(
                    f"[{channel_name}] Reply target TG message {tg_reply_to} not found in DB "
                    f"(may pre-date bot or failed to send)"
                )

        # Raw message for archive (serialise safely)
        try:
            raw_message = msg.to_dict()
        except Exception:
            raw_message = None

        # ---------------------------------------------------------------------------
        # AI triage — optionally filter / rewrite the message before forwarding
        # ---------------------------------------------------------------------------
        triage_action   = "forward"
        triage_reason   = None
        
        # Pre-processing: Remove French disclaimer BEFORE AI processing
        if "France Trading Pro" in channel_name and message_text:
            disclaimers = [
                "⚠️ Ceci n'est pas un conseil financier, faites vos propres recherche.",
                "Ceci n'est pas un conseil financier, faites vos propres recherche.",
                "⚠️ Ceci n'est pas un conseil financier",
                "Ceci n'est pas un conseil financier",
            ]
            for disclaimer in disclaimers:
                if disclaimer in message_text:
                    message_text = message_text.replace(disclaimer, "").strip()
                    if should_log_verbose(db_channel_id):
                        logger.info(f"[{channel_name}] Removed French disclaimer (pre-AI)")
                    break
        
        if ai_enabled and ai_api_key and message_text:
            triage = await triage_message(
                message_text  = message_text,
                channel_name  = channel_name,
                triage_prompt = ai_triage_prompt,
                format_prompt = ai_format_prompt,
                provider      = use_provider,  # Use per-channel or global provider
                model         = use_model,      # Use per-channel or global model
                api_key       = ai_api_key,
                is_reply      = (tg_reply_to is not None),
                parent_message_text = quoted_text,
                channel_id    = db_channel_id,
                verbose_logging = should_log_verbose(db_channel_id),
            )
            triage_action = triage.action
            triage_reason = triage.reason
            if triage.rewritten_text:
                message_text = triage.rewritten_text

        if triage_action == "discard":
            if should_log_verbose(db_channel_id):
                logger.info(f"AI discarded message from '{channel_name}': {triage_reason}")
            return

        # Send to Discord
        # Note: Don't pass quoted_text if AI is enabled - the AI already processed
        # and translated everything, so showing raw quoted text would include untranslated content
        discord_message_id, discord_text_sent = await send_to_discord(
            webhook_url,
            message_text,
            media_path,
            reply_to_discord_id,
            role_id,
            discord_channel_id,
            discord_guild_id,
            quoted_text if not ai_enabled else None,  # Suppress quoted text for AI channels
            db_channel_id,
        )

        # Archive to DB
        send_status = "sent" if discord_message_id else "failed"
        db.save_message(
            channel_id           = db_channel_id,
            telegram_message_id  = tg_msg_id,
            telegram_reply_to    = tg_reply_to,
            sender_id            = sender_id,
            sender_name          = sender_name,
            message_text         = message_text or None,
            media_type           = media_type,
            media_file_name      = media_file_name,
            raw_message          = raw_message,
            discord_message_id   = discord_message_id,
            formatted_message    = discord_text_sent,
            discord_username     = bot_username,
            discord_webhook      = webhook_url,
            send_status          = send_status,
            error_detail         = None if send_status == "sent" else "send returned no message id",
        )

        if discord_message_id:
            if should_log_verbose(db_channel_id):
                logger.info(
                    f"Forwarded message from '{channel_name}' → Discord ({discord_message_id})"
                )
        else:
            logger.warning(
                f"Message from '{channel_name}' archived but Discord send failed."
            )

    except Exception as e:
        logger.error(f"Error processing message: {e}", exc_info=True)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def main():
    try:
        resolved = await resolve_channels()
        if not resolved:
            logger.error("No channels could be resolved. Exiting...")
            return

        # Register event handler with resolved numeric IDs
        resolved_ids = list(channel_webhook_map.keys())
        client.add_event_handler(
            handle_new_message,
            events.NewMessage(chats=resolved_ids),
        )

        logger.info(
            f"Monitoring {len(resolved)} channel(s): "
            + ", ".join(c["name"] for c in channel_webhook_map.values())
        )
        logger.info("Bot started and listening for messages...")
        await client.run_until_disconnected()

    except Exception as e:
        logger.error(f"Main loop error: {e}", exc_info=True)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

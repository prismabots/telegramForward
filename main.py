from telethon import TelegramClient, events
from telethon.tl.functions.messages import CheckChatInviteRequest
import requests
import logging
from datetime import datetime
import os
import tempfile
import mimetypes
import json
import sys

# Ensure db module is importable from the same directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import db

# ---------------------------------------------------------------------------
# Logging setup (basic level first; overridden after DB load below)
# ---------------------------------------------------------------------------
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

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
for ch in db_channels:
    channel_configs[ch["chat_id"]] = {
        "webhook": ch["discord_webhook"],
        "name":    ch["name"],
        "db_id":   ch["id"],
        "role_id": ch.get("discord_role_id"),
    }
    logger.info(f"Loaded channel from DB: {ch['name']} ({ch['chat_id']})")

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
) -> tuple[str | None, str | None]:
    """
    Send a message (and optional media) to a Discord webhook.

    Uses ?wait=true so Discord returns the created message object,
    allowing us to capture the discord_message_id for reply threading.

    If role_id is provided, a role mention is prepended to the message
    so Discord notifies subscribers of that role.

    Returns:
        (discord_message_id, actual_text_sent) or (None, None) on failure.
    """
    # Prepend role mention if configured
    role_mention = f"<@&{role_id}>\n" if role_id else ""

    # Append ?wait=true to get response body with message id
    url = webhook_url.rstrip("/") + ("&" if "?" in webhook_url else "?") + "wait=true"

    # Build message_reference payload if this is a reply
    message_reference = None
    if reply_to_discord_id:
        message_reference = {"message_id": reply_to_discord_id}

    try:
        if media_path:
            mime_type, _ = mimetypes.guess_type(media_path)
            ext = get_file_extension(media_path)

            if is_image(media_path):
                filename     = f"image{ext or '.png'}"
                content_type = mime_type or "image/png"
                fallback_text = "Image from Telegram"
            elif is_video(media_path):
                filename     = f"video{ext or '.mp4'}"
                content_type = mime_type or "video/mp4"
                fallback_text = "Video from Telegram"
            else:
                filename     = f"file{ext}"
                content_type = mime_type or "application/octet-stream"
                fallback_text = "File from Telegram"

            text = role_mention + (message_text if message_text else fallback_text)
            payload: dict = {"content": text, "username": bot_username, "flags": 4}
            if message_reference:
                payload["message_reference"] = message_reference

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
            text = role_mention + message_text
            payload = {"content": text, "username": bot_username, "flags": 4}
            if message_reference:
                payload["message_reference"] = message_reference
            response = requests.post(url, json=payload)

        response.raise_for_status()
        resp_json          = response.json()
        discord_message_id = str(resp_json.get("id", ""))
        logger.info(f"Sent to Discord — discord_message_id={discord_message_id}")
        return discord_message_id or None, text

    except Exception as e:
        logger.error(f"Failed to send message to Discord: {e}")
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
                "webhook": cfg["webhook"],
                "name":    cfg["name"],
                "db_id":   cfg["db_id"],
                "role_id": cfg["role_id"],
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

        webhook_url   = cfg["webhook"]
        channel_name  = cfg["name"]
        db_channel_id = cfg["db_id"]
        role_id       = cfg.get("role_id")

        msg          = event.message
        message_text = msg.text or ""
        tg_msg_id    = msg.id
        tg_reply_to  = getattr(msg.reply_to, "reply_to_msg_id", None) if msg.reply_to else None

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
            reply_to_discord_id = db.get_discord_msg_id(db_channel_id, tg_reply_to)
            if reply_to_discord_id:
                logger.info(
                    f"Threading: TG {tg_reply_to} → Discord {reply_to_discord_id}"
                )

        # Raw message for archive (serialise safely)
        try:
            raw_message = msg.to_dict()
        except Exception:
            raw_message = None

        # Send to Discord
        discord_message_id, discord_text_sent = await send_to_discord(
            webhook_url,
            message_text,
            media_path,
            reply_to_discord_id,
            role_id,
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
            discord_message_text = discord_text_sent,
            discord_username     = bot_username,
            discord_webhook      = webhook_url,
            send_status          = send_status,
            error_detail         = None if send_status == "sent" else "send returned no message id",
        )

        if discord_message_id:
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

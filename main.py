from telethon import TelegramClient, events
import requests
import logging
from datetime import datetime
import os
import tempfile
import mimetypes
import json
import sys

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")


def load_config():
    """Load configuration from config.json"""
    if not os.path.exists(CONFIG_PATH):
        logger.error(f"Config file not found: {CONFIG_PATH}")
        logger.error("Copy config.json.example to config.json and fill in your values.")
        sys.exit(1)

    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config = json.load(f)

    # Validate required fields
    tg = config.get("telegram", {})
    if not tg.get("api_id") or not tg.get("api_hash"):
        logger.error("telegram.api_id and telegram.api_hash are required in config.json")
        sys.exit(1)

    channels = config.get("channels", [])
    enabled = [ch for ch in channels if ch.get("enabled", True)]
    if not enabled:
        logger.error("No enabled channels found in config.json")
        sys.exit(1)

    for ch in enabled:
        if not ch.get("chat_id") or not ch.get("discord_webhook"):
            logger.error(f"Channel entry missing chat_id or discord_webhook: {ch}")
            sys.exit(1)

    return config


# Logging setup
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Load config
config = load_config()

# Apply log level from config
log_level = config.get("log_level", "INFO").upper()
logging.getLogger().setLevel(getattr(logging, log_level, logging.INFO))

# Telegram settings
tg_config = config["telegram"]
api_id = int(tg_config["api_id"])
api_hash = tg_config["api_hash"]
session_name = tg_config.get("session_name", "anon")

# Bot display name for Discord
bot_username = config.get("bot_username", "Telegram Forward Bot")

# Build channel -> webhook mapping (only enabled channels)
channel_webhook_map = {}
for ch in config["channels"]:
    if ch.get("enabled", True):
        channel_webhook_map[ch["chat_id"]] = {
            "webhook": ch["discord_webhook"],
            "name": ch.get("name", ch["chat_id"]),
        }

# List of chat IDs to listen to
monitored_chats = list(channel_webhook_map.keys())

# Initialize the Telegram client
client = TelegramClient(session_name, api_id, api_hash)


def is_video(file_path):
    """Check if the file is a video based on its mimetype"""
    mime_type, _ = mimetypes.guess_type(file_path)
    return mime_type and mime_type.startswith("video")


def is_image(file_path):
    """Check if the file is an image based on its mimetype"""
    mime_type, _ = mimetypes.guess_type(file_path)
    return mime_type and mime_type.startswith("image")


def get_file_extension(file_path):
    """Get file extension or fallback"""
    _, ext = os.path.splitext(file_path)
    return ext if ext else ""


async def send_to_discord(webhook_url, message_text, media_path=None):
    """Send a message and optional media to a Discord webhook"""
    try:
        if media_path:
            mime_type, _ = mimetypes.guess_type(media_path)
            ext = get_file_extension(media_path)

            if is_image(media_path):
                filename = f"image{ext or '.png'}"
                content_type = mime_type or "image/png"
                fallback_text = "Image from Telegram"
            elif is_video(media_path):
                filename = f"video{ext or '.mp4'}"
                content_type = mime_type or "video/mp4"
                fallback_text = "Video from Telegram"
            else:
                filename = f"file{ext}"
                content_type = mime_type or "application/octet-stream"
                fallback_text = "File from Telegram"

            text = message_text if message_text else fallback_text
            data = {"content": text, "username": bot_username}

            with open(media_path, "rb") as file:
                files = {"file": (filename, file, content_type)}
                response = requests.post(
                    webhook_url,
                    data={"payload_json": json.dumps(data)},
                    files=files,
                )
        else:
            if not message_text:
                return
            data = {"content": message_text, "username": bot_username}
            response = requests.post(webhook_url, json=data)

        response.raise_for_status()
        logger.info("Successfully sent message to Discord")
    except Exception as e:
        logger.error(f"Failed to send message to Discord: {e}")
    finally:
        if media_path and os.path.exists(media_path):
            try:
                os.remove(media_path)
            except Exception as e:
                logger.error(f"Failed to clean up media file: {e}")


async def resolve_channels():
    """Resolve and join all monitored channels"""
    await client.start()
    resolved = []
    for chat_id in monitored_chats:
        try:
            entity = await client.get_entity(f"https://t.me/{chat_id}")
            name = channel_webhook_map[chat_id]["name"]
            logger.info(f"Resolved channel: {name} ({chat_id})")
            resolved.append(entity)
        except Exception as e:
            name = channel_webhook_map[chat_id]["name"]
            logger.error(f"Failed to resolve channel '{name}' ({chat_id}): {e}")
    return resolved


async def download_media_to_temp(message):
    """Download media to a temporary file and return the path"""
    try:
        if message.media:
            temp_dir = tempfile.gettempdir()
            temp_path = os.path.join(
                temp_dir, f'tgfwd_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
            )
            path = await message.download_media(temp_path)
            logger.info(f"Media downloaded to {path}")
            return path
    except Exception as e:
        logger.error(f"Failed to download media: {e}")
    return None


@client.on(events.NewMessage(chats=monitored_chats))
async def handler(event):
    try:
        chat = await event.get_chat()
        if not chat or not hasattr(chat, "id"):
            return

        # Determine which webhook to use based on the chat
        chat_username = getattr(chat, "username", None)
        webhook_url = None

        # Try matching by username first
        if chat_username and chat_username in channel_webhook_map:
            webhook_url = channel_webhook_map[chat_username]["webhook"]
            channel_name = channel_webhook_map[chat_username]["name"]
        else:
            # Try matching by chat ID string
            for key, value in channel_webhook_map.items():
                try:
                    if str(chat.id) == str(key):
                        webhook_url = value["webhook"]
                        channel_name = value["name"]
                        break
                except Exception:
                    pass

        if not webhook_url:
            # Fallback: try all keys
            for key, value in channel_webhook_map.items():
                try:
                    entity = await client.get_entity(f"https://t.me/{key}")
                    if entity.id == chat.id:
                        webhook_url = value["webhook"]
                        channel_name = value["name"]
                        break
                except Exception:
                    continue

        if not webhook_url:
            logger.warning(f"No webhook found for chat {chat.id}")
            return

        message_text = event.message.text or ""

        media_path = None
        if event.message.media:
            media_path = await download_media_to_temp(event.message)

        await send_to_discord(webhook_url, message_text, media_path)
        logger.info(f"Forwarded message from '{channel_name}' to Discord")

    except Exception as e:
        logger.error(f"Error processing message: {e}", exc_info=True)


async def main():
    try:
        channels = await resolve_channels()
        if not channels:
            logger.error("No channels could be resolved. Exiting...")
            return

        logger.info(
            f"Monitoring {len(channels)} channel(s): "
            + ", ".join(channel_webhook_map[c]["name"] for c in monitored_chats)
        )
        logger.info("Bot started and listening for messages...")
        await client.run_until_disconnected()
    except Exception as e:
        logger.error(f"Main loop error: {e}", exc_info=True)


if __name__ == "__main__":
    client.loop.run_until_complete(main())

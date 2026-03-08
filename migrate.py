"""
migrate.py — One-time migration script.

Reads the current .env file (CHANNEL_<n>_* variables) and seeds the
PostgreSQL database.  Run this once on a machine that still has the .env
file, then rely on the DB from that point on.

Usage:
    python migrate.py
"""

import os
import sys
import logging
from dotenv import dotenv_values

# Make sure db module is importable from the same directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import db

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

ENV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")


def main():
    if not os.environ.get("BACKUP_DB_ADMIN_URL"):
        logger.error("BACKUP_DB_ADMIN_URL environment variable is not set.")
        logger.error("This is injected by DigitalOcean — set it in your shell before running migrate.py")
        sys.exit(1)

    if not os.path.exists(ENV_PATH):
        logger.error(f".env file not found at {ENV_PATH}")
        sys.exit(1)

    # Read .env without affecting os.environ
    env = dotenv_values(ENV_PATH)

    # -----------------------------------------------------------------------
    # 1. Initialise schema
    # -----------------------------------------------------------------------
    logger.info("Initialising database schema...")
    db.init_db()

    # -----------------------------------------------------------------------
    # 2. Migrate settings
    # -----------------------------------------------------------------------
    setting_map = {
        "TELEGRAM_API_ID":       "telegram_api_id",
        "TELEGRAM_API_HASH":     "telegram_api_hash",
        "TELEGRAM_SESSION_NAME": "telegram_session_name",
        "BOT_USERNAME":          "bot_username",
        "LOG_LEVEL":             "log_level",
    }

    logger.info("Migrating settings...")
    migrated_settings = 0
    for env_key, db_key in setting_map.items():
        value = env.get(env_key)
        if value:
            db.set_setting(db_key, value)
            logger.info(f"  ✓ {db_key} = {value if 'hash' not in db_key.lower() else '***'}")
            migrated_settings += 1
        else:
            logger.info(f"  – {db_key} not in .env, keeping DB default")

    # -----------------------------------------------------------------------
    # 3. Migrate channels
    # -----------------------------------------------------------------------
    logger.info("Migrating channels...")
    migrated_channels = 0
    skipped_channels = 0
    i = 1

    while True:
        chat_id = env.get(f"CHANNEL_{i}_CHAT_ID")
        if not chat_id:
            break

        webhook = env.get(f"CHANNEL_{i}_WEBHOOK")
        name    = env.get(f"CHANNEL_{i}_NAME", chat_id)
        enabled = env.get(f"CHANNEL_{i}_ENABLED", "true").lower() == "true"

        if not webhook:
            logger.warning(f"  ⚠  CHANNEL_{i}_CHAT_ID set but no CHANNEL_{i}_WEBHOOK — skipping")
            i += 1
            continue

        # Check if already exists
        existing = db.get_channels(enabled_only=False)
        already = any(ch["chat_id"] == chat_id for ch in existing)

        if already:
            logger.info(f"  – Channel '{name}' ({chat_id}) already in DB — skipping")
            skipped_channels += 1
        else:
            db.add_channel(name=name, chat_id=chat_id, discord_webhook=webhook, enabled=enabled)
            status = "enabled" if enabled else "disabled"
            logger.info(f"  ✓ Added '{name}' ({chat_id}) [{status}]")
            migrated_channels += 1

        i += 1

    # -----------------------------------------------------------------------
    # 4. Summary
    # -----------------------------------------------------------------------
    logger.info("")
    logger.info("=" * 50)
    logger.info("Migration complete!")
    logger.info(f"  Settings migrated : {migrated_settings}")
    logger.info(f"  Channels added    : {migrated_channels}")
    logger.info(f"  Channels skipped  : {skipped_channels}")
    logger.info("=" * 50)
    logger.info("")
    logger.info("You can now run 'python main.py' — the .env file is no longer")
    logger.info("needed at runtime (DATABASE_URL still required from the environment).")


if __name__ == "__main__":
    main()

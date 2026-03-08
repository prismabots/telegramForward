"""
db.py — PostgreSQL database layer for telegramForward.

Connection is established via the BACKUP_DB_ADMIN_URL environment variable,
which is injected automatically by DigitalOcean App Platform.  Everything
else (Telegram credentials, bot settings, channel rules) lives in the database.
"""

import os
import json
import logging
import datetime
import psycopg2
import psycopg2.extras
from psycopg2 import pool

logger = logging.getLogger(__name__)


class _TelegramEncoder(json.JSONEncoder):
    """JSON encoder that handles types returned by Telethon's to_dict()."""

    def default(self, obj):
        if isinstance(obj, (datetime.datetime, datetime.date)):
            return obj.isoformat()
        if isinstance(obj, bytes):
            return obj.hex()
        # Fallback: convert to string rather than crashing
        try:
            return super().default(obj)
        except TypeError:
            return str(obj)

# ---------------------------------------------------------------------------
# Connection pool
# ---------------------------------------------------------------------------

_pool: pool.SimpleConnectionPool | None = None


def _get_pool() -> pool.SimpleConnectionPool:
    """Return the global connection pool, creating it on first call."""
    global _pool
    if _pool is None or _pool.closed:
        url = os.environ.get("BACKUP_DB_ADMIN_URL")
        if not url:
            raise RuntimeError("BACKUP_DB_ADMIN_URL environment variable is not set.")
        _pool = pool.SimpleConnectionPool(
            minconn=1,
            maxconn=5,   # keep well within DigitalOcean's connection limit
            dsn=url,
        )
        logger.info("Database connection pool created (min=1, max=5).")
    return _pool


def get_connection():
    """Borrow a connection from the pool."""
    return _get_pool().getconn()


def release_connection(conn):
    """Return a connection to the pool."""
    try:
        _get_pool().putconn(conn)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Schema initialisation
# ---------------------------------------------------------------------------

_DDL = """
CREATE TABLE IF NOT EXISTS tele_settings (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS tele_channels (
    id                  SERIAL      PRIMARY KEY,
    name                TEXT        NOT NULL,
    chat_id             TEXT        NOT NULL UNIQUE,
    telegram_channel_id BIGINT      UNIQUE,
    discord_webhook     TEXT        NOT NULL,
    discord_role_id     TEXT,
    ai_enabled          BOOLEAN     NOT NULL DEFAULT FALSE,
    ai_triage_prompt    TEXT,
    ai_format_prompt    TEXT,
    enabled             BOOLEAN     NOT NULL DEFAULT TRUE,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Idempotent: add discord_role_id if this is an existing DB
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'tele_channels' AND column_name = 'discord_role_id'
    ) THEN
        ALTER TABLE tele_channels ADD COLUMN discord_role_id TEXT;
    END IF;
END $$;

-- Idempotent: add ai_enabled if this is an existing DB
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'tele_channels' AND column_name = 'ai_enabled'
    ) THEN
        ALTER TABLE tele_channels ADD COLUMN ai_enabled BOOLEAN NOT NULL DEFAULT FALSE;
    END IF;
END $$;

-- Idempotent: rename ai_prompt -> ai_triage_prompt if old column still exists
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'tele_channels' AND column_name = 'ai_prompt'
    ) THEN
        ALTER TABLE tele_channels RENAME COLUMN ai_prompt TO ai_triage_prompt;
    END IF;
END $$;

-- Idempotent: add ai_triage_prompt if this is a fresh DB
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'tele_channels' AND column_name = 'ai_triage_prompt'
    ) THEN
        ALTER TABLE tele_channels ADD COLUMN ai_triage_prompt TEXT;
    END IF;
END $$;

-- Idempotent: add ai_format_prompt if this is an existing DB
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'tele_channels' AND column_name = 'ai_format_prompt'
    ) THEN
        ALTER TABLE tele_channels ADD COLUMN ai_format_prompt TEXT;
    END IF;
END $$;

CREATE TABLE IF NOT EXISTS tele_messages (
    id                   SERIAL      PRIMARY KEY,
    channel_id           INTEGER     NOT NULL REFERENCES tele_channels(id) ON DELETE CASCADE,

    -- Telegram side
    telegram_message_id  BIGINT      NOT NULL,
    telegram_reply_to    BIGINT,
    sender_id            BIGINT,
    sender_name          TEXT,
    message_text         TEXT,
    media_type           TEXT,
    media_file_name      TEXT,
    raw_message          JSONB,

    -- Discord side
    discord_message_id   TEXT,
    discord_message_text TEXT,
    discord_username     TEXT,
    discord_webhook      TEXT        NOT NULL,
    send_status          TEXT        NOT NULL DEFAULT 'sent',
    error_detail         TEXT,

    created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (channel_id, telegram_message_id)
);

CREATE INDEX IF NOT EXISTS idx_tele_messages_channel_tg
    ON tele_messages (channel_id, telegram_message_id);

CREATE INDEX IF NOT EXISTS idx_tele_messages_reply_to
    ON tele_messages (channel_id, telegram_reply_to);
"""

_DEFAULT_SETTINGS = {
    "bot_username": "Telegram Forward Bot",
    "log_level": "INFO",
    "telegram_session_name": "anon",
}


def init_db():
    """Create tables and seed default settings if they don't exist."""
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(_DDL)
                for key, value in _DEFAULT_SETTINGS.items():
                    cur.execute(
                        "INSERT INTO tele_settings (key, value) VALUES (%s, %s) "
                        "ON CONFLICT (key) DO NOTHING",
                        (key, value),
                    )
        logger.info("Database initialised successfully.")
    finally:
        release_connection(conn)


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

def get_setting(key: str, default=None) -> str | None:
    """Fetch a single setting value by key."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT value FROM tele_settings WHERE key = %s", (key,))
            row = cur.fetchone()
            return row[0] if row else default
    finally:
        release_connection(conn)


def set_setting(key: str, value: str) -> None:
    """Upsert a setting value."""
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO tele_settings (key, value) VALUES (%s, %s) "
                    "ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value",
                    (key, value),
                )
    finally:
        release_connection(conn)


def get_all_settings() -> dict:
    """Return all settings as a plain dict."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT key, value FROM tele_settings")
            return {row[0]: row[1] for row in cur.fetchall()}
    finally:
        release_connection(conn)


# ---------------------------------------------------------------------------
# Channels
# ---------------------------------------------------------------------------

def get_channels(enabled_only: bool = True) -> list[dict]:
    """Return channel rows as a list of dicts."""
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            if enabled_only:
                cur.execute(
                    "SELECT * FROM tele_channels WHERE enabled = TRUE ORDER BY id"
                )
            else:
                cur.execute("SELECT * FROM tele_channels ORDER BY id")
            return [dict(row) for row in cur.fetchall()]
    finally:
        release_connection(conn)


def add_channel(
    name: str,
    chat_id: str,
    discord_webhook: str,
    enabled: bool = True,
) -> dict:
    """Insert a new channel and return the created row."""
    conn = get_connection()
    try:
        with conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    """
                    INSERT INTO tele_channels (name, chat_id, discord_webhook, enabled)
                    VALUES (%s, %s, %s, %s)
                    RETURNING *
                    """,
                    (name, chat_id, discord_webhook, enabled),
                )
                return dict(cur.fetchone())
    finally:
        release_connection(conn)


def update_channel(channel_id: int, **kwargs) -> dict | None:
    """
    Update one or more columns on a channel row.
    Accepted kwargs: name, chat_id, discord_webhook, enabled, telegram_channel_id, discord_role_id
    """
    allowed = {"name", "chat_id", "discord_webhook", "enabled", "telegram_channel_id", "discord_role_id", "ai_enabled", "ai_triage_prompt", "ai_format_prompt"}
    fields = {k: v for k, v in kwargs.items() if k in allowed}
    if not fields:
        return None

    set_clause = ", ".join(f"{k} = %s" for k in fields)
    values = list(fields.values()) + [channel_id]

    conn = get_connection()
    try:
        with conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    f"UPDATE tele_channels SET {set_clause} WHERE id = %s RETURNING *",
                    values,
                )
                row = cur.fetchone()
                return dict(row) if row else None
    finally:
        release_connection(conn)


def delete_channel(channel_id: int) -> bool:
    """Delete a channel by id. Returns True if a row was deleted."""
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM tele_channels WHERE id = %s", (channel_id,)
                )
                return cur.rowcount > 0
    finally:
        release_connection(conn)


# ---------------------------------------------------------------------------
# Message archive + reply threading
# ---------------------------------------------------------------------------

def save_message(
    *,
    channel_id: int,
    telegram_message_id: int,
    telegram_reply_to: int | None,
    sender_id: int | None,
    sender_name: str | None,
    message_text: str | None,
    media_type: str | None,
    media_file_name: str | None,
    raw_message: dict | None,
    discord_message_id: str | None,
    discord_message_text: str | None,
    discord_username: str | None,
    discord_webhook: str,
    send_status: str = "sent",
    error_detail: str | None = None,
) -> None:
    """Insert a forwarded message into the archive."""
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO tele_messages (
                        channel_id, telegram_message_id, telegram_reply_to,
                        sender_id, sender_name,
                        message_text, media_type, media_file_name, raw_message,
                        discord_message_id, discord_message_text, discord_username,
                        discord_webhook, send_status, error_detail
                    ) VALUES (
                        %s, %s, %s,
                        %s, %s,
                        %s, %s, %s, %s,
                        %s, %s, %s,
                        %s, %s, %s
                    )
                    ON CONFLICT (channel_id, telegram_message_id) DO NOTHING
                    """,
                    (
                        channel_id,
                        telegram_message_id,
                        telegram_reply_to,
                        sender_id,
                        sender_name,
                        message_text,
                        media_type,
                        media_file_name,
                        json.dumps(raw_message, cls=_TelegramEncoder) if raw_message else None,
                        discord_message_id,
                        discord_message_text,
                        discord_username,
                        discord_webhook,
                        send_status,
                        error_detail,
                    ),
                )
    finally:
        release_connection(conn)


def get_discord_msg_id(channel_id: int, telegram_message_id: int) -> str | None:
    """
    Look up the Discord message ID that corresponds to a Telegram message.
    Returns None if not found (e.g. message pre-dates the bot).
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT discord_message_id
                FROM tele_messages
                WHERE channel_id = %s
                  AND telegram_message_id = %s
                  AND discord_message_id IS NOT NULL
                """,
                (channel_id, telegram_message_id),
            )
            row = cur.fetchone()
            return row[0] if row else None
    finally:
        release_connection(conn)

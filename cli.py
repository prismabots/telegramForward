"""
cli.py — Command-line management tool for telegramForward.

Manages channels and settings stored in the PostgreSQL database.
DATABASE_URL must be set as an environment variable.

Usage examples:
    python cli.py channel list
    python cli.py channel add --name "Trading Signals" --chat-id tradingSignals --webhook https://...
    python cli.py channel enable 1
    python cli.py channel disable 1
    python cli.py channel delete 1
    python cli.py setting list
    python cli.py setting get bot_username
    python cli.py setting set log_level DEBUG
"""

import os
import sys
import argparse
import logging

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import db

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.WARNING,  # Keep CLI output clean
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _check_db_url():
    if not os.environ.get("DATABASE_URL"):
        print("ERROR: DATABASE_URL environment variable is not set.", file=sys.stderr)
        sys.exit(1)


def _print_channel(ch: dict):
    status      = "✓ enabled" if ch["enabled"] else "✗ disabled"
    tg_id       = ch.get("telegram_channel_id") or "not yet resolved"
    print(
        f"  [{ch['id']}] {ch['name']}\n"
        f"       chat_id      : {ch['chat_id']}\n"
        f"       telegram_id  : {tg_id}\n"
        f"       webhook      : {ch['discord_webhook']}\n"
        f"       status       : {status}\n"
        f"       created      : {ch['created_at']}"
    )


# ---------------------------------------------------------------------------
# Channel subcommands
# ---------------------------------------------------------------------------

def cmd_channel_list(_args):
    channels = db.get_channels(enabled_only=False)
    if not channels:
        print("No channels configured.")
        return
    print(f"\n{'─'*60}")
    for ch in channels:
        _print_channel(ch)
        print(f"{'─'*60}")
    print(f"Total: {len(channels)} channel(s)\n")


def cmd_channel_add(args):
    ch = db.add_channel(
        name            = args.name,
        chat_id         = args.chat_id,
        discord_webhook = args.webhook,
        enabled         = not args.disabled,
    )
    print(f"Channel added with ID {ch['id']}: {ch['name']} ({ch['chat_id']})")


def cmd_channel_enable(args):
    result = db.update_channel(args.id, enabled=True)
    if result:
        print(f"Channel {args.id} ({result['name']}) enabled.")
    else:
        print(f"Channel ID {args.id} not found.", file=sys.stderr)
        sys.exit(1)


def cmd_channel_disable(args):
    result = db.update_channel(args.id, enabled=False)
    if result:
        print(f"Channel {args.id} ({result['name']}) disabled.")
    else:
        print(f"Channel ID {args.id} not found.", file=sys.stderr)
        sys.exit(1)


def cmd_channel_delete(args):
    confirm = input(f"Delete channel ID {args.id}? This also deletes all archived messages. [y/N] ")
    if confirm.lower() != "y":
        print("Aborted.")
        return
    deleted = db.delete_channel(args.id)
    if deleted:
        print(f"Channel {args.id} deleted.")
    else:
        print(f"Channel ID {args.id} not found.", file=sys.stderr)
        sys.exit(1)


# ---------------------------------------------------------------------------
# Setting subcommands
# ---------------------------------------------------------------------------

def cmd_setting_list(_args):
    settings = db.get_all_settings()
    if not settings:
        print("No settings found.")
        return
    print()
    for key, value in sorted(settings.items()):
        display = "***" if "hash" in key.lower() or "api" in key.lower() else value
        print(f"  {key:30s} = {display}")
    print()


def cmd_setting_get(args):
    value = db.get_setting(args.key)
    if value is None:
        print(f"Setting '{args.key}' not found.", file=sys.stderr)
        sys.exit(1)
    display = "***" if "hash" in args.key.lower() or "api" in args.key.lower() else value
    print(f"{args.key} = {display}")


def cmd_setting_set(args):
    db.set_setting(args.key, args.value)
    print(f"Setting '{args.key}' updated.")


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cli.py",
        description="Manage telegramForward config stored in PostgreSQL.",
    )
    sub = parser.add_subparsers(dest="resource", required=True)

    # ── channel ──────────────────────────────────────────────────────────
    ch_parser = sub.add_parser("channel", help="Manage forwarding channels")
    ch_sub = ch_parser.add_subparsers(dest="action", required=True)

    ch_sub.add_parser("list", help="List all channels")

    add_p = ch_sub.add_parser("add", help="Add a new channel")
    add_p.add_argument("--name",     required=True, help="Display name for logging")
    add_p.add_argument("--chat-id",  required=True, dest="chat_id",
                       help="Telegram username or +invite_code")
    add_p.add_argument("--webhook",  required=True, help="Discord webhook URL")
    add_p.add_argument("--disabled", action="store_true",
                       help="Add channel in disabled state")

    enable_p = ch_sub.add_parser("enable", help="Enable a channel by ID")
    enable_p.add_argument("id", type=int)

    disable_p = ch_sub.add_parser("disable", help="Disable a channel by ID")
    disable_p.add_argument("id", type=int)

    delete_p = ch_sub.add_parser("delete", help="Delete a channel by ID")
    delete_p.add_argument("id", type=int)

    # ── setting ───────────────────────────────────────────────────────────
    st_parser = sub.add_parser("setting", help="Manage global settings")
    st_sub = st_parser.add_subparsers(dest="action", required=True)

    st_sub.add_parser("list", help="List all settings")

    get_p = st_sub.add_parser("get", help="Get a setting value")
    get_p.add_argument("key")

    set_p = st_sub.add_parser("set", help="Set a setting value")
    set_p.add_argument("key")
    set_p.add_argument("value")

    return parser


# ---------------------------------------------------------------------------
# Dispatch table
# ---------------------------------------------------------------------------

_COMMANDS = {
    ("channel", "list"):    cmd_channel_list,
    ("channel", "add"):     cmd_channel_add,
    ("channel", "enable"):  cmd_channel_enable,
    ("channel", "disable"): cmd_channel_disable,
    ("channel", "delete"):  cmd_channel_delete,
    ("setting", "list"):    cmd_setting_list,
    ("setting", "get"):     cmd_setting_get,
    ("setting", "set"):     cmd_setting_set,
}


def main():
    _check_db_url()
    parser = build_parser()
    args = parser.parse_args()

    fn = _COMMANDS.get((args.resource, args.action))
    if fn is None:
        parser.print_help()
        sys.exit(1)

    fn(args)


if __name__ == "__main__":
    main()

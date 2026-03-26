#!/usr/bin/env python3
"""
add_channel.py — Interactive script to add a new Telegram→Discord forwarding channel.

Usage:
    python add_channel.py

    # Or with command-line args (non-interactive):
    python add_channel.py \
        --name "My Channel" \
        --chat-id "-1001234567890" \
        --webhook "https://discord.com/api/webhooks/..." \
        --template t2t \
        --role-id "1480307797261287714"

Templates:
    t2t      → T2T Gold / Forex (crypto/forex signal filter + formatter)
    spx      → SPX Options AI (Arabic/English SPX options signals)
    algo     → Algo Pro (algorithmic trading signals)
    france   → France Trading Pro (French-language forex signals)
    none     → No AI (just forward raw messages)
"""

import os
import sys
import argparse
import db

# ─────────────────────────────────────────────────────────────────────────────
# Known role IDs for quick reference
# ─────────────────────────────────────────────────────────────────────────────
KNOWN_ROLES = {
    "forex":  "1480307797261287714",   # Main Forex role (T2T Gold, Forex Trading, etc.)
    "spx":    "1392269045226668227",   # SPX Options role
}

# ─────────────────────────────────────────────────────────────────────────────
# Templates — copy AI config from existing channels by name pattern
# ─────────────────────────────────────────────────────────────────────────────
TEMPLATES = {
    "t2t":    {"search": "T2T",     "description": "T2T Gold (Forex/Crypto signals)"},
    "spx":    {"search": "SPX",     "description": "SPX Options AI (Arabic/English options)"},
    "algo":   {"search": "Algo",    "description": "Algo Pro (algorithmic signals)"},
    "france": {"search": "France",  "description": "France Trading Pro (French forex)"},
    "none":   {"search": None,      "description": "No AI (raw forwarding only)"},
}


def load_template(template_key: str) -> dict | None:
    """Load AI config from the matching template channel."""
    if template_key == "none":
        return None

    search = TEMPLATES[template_key]["search"]
    channels = db.get_channels(enabled_only=False)
    source = next((ch for ch in channels if search in ch["name"]), None)

    if not source:
        print(f"⚠  Warning: Template channel matching '{search}' not found. No AI config will be applied.")
        return None

    print(f"  ✓ Using template: '{source['name']}' (ID {source['id']})")
    return source


def list_existing_channels():
    """Print all existing channels in a table."""
    channels = db.get_channels(enabled_only=False)
    print()
    print(f"{'ID':<4} {'Name':<35} {'Chat ID':<22} {'AI':<5} {'Role'}")
    print("─" * 95)
    for ch in channels:
        ai = "✓" if ch["ai_enabled"] else "✗"
        role = ch["discord_role_id"] or "—"
        print(f"{ch['id']:<4} {ch['name']:<35} {ch['chat_id']:<22} {ai:<5} {role}")
    print()


def add_channel(
    name: str,
    chat_id: str,
    webhook: str,
    template_key: str = "t2t",
    role_id: str | None = None,
    dry_run: bool = False,
):
    """Add a new channel with the given configuration."""

    # Validate chat_id format
    if not chat_id.startswith("-"):
        print("⚠  Warning: chat_id should typically start with '-' for Telegram group/channel IDs")

    # Check for duplicate
    channels = db.get_channels(enabled_only=False)
    existing = next((ch for ch in channels if ch["chat_id"] == chat_id), None)
    if existing:
        print(f"✗  Channel with chat_id {chat_id} already exists: '{existing['name']}' (ID {existing['id']})")
        sys.exit(1)

    # Load template
    source = load_template(template_key)

    # Preview
    print()
    print("─" * 60)
    print("NEW CHANNEL SUMMARY")
    print("─" * 60)
    print(f"  Name:            {name}")
    print(f"  Telegram Chat ID: {chat_id}")
    print(f"  Discord Webhook: {webhook[:55]}...")
    print(f"  Discord Role ID: {role_id or '(none)'}")
    print(f"  AI Enabled:      {'Yes' if source is not None or template_key != 'none' else 'No'}")
    print(f"  AI Template:     {TEMPLATES[template_key]['description']}")
    if source:
        print(f"  Triage Prompt:   {'SET' if source.get('ai_triage_prompt') else 'NOT SET'}")
        print(f"  Format Prompt:   {'SET' if source.get('ai_format_prompt') else 'NOT SET'}")
        print(f"  Fallback AI:     {source.get('ai_fallback_provider')}/{source.get('ai_fallback_model')}")
    print("─" * 60)

    if dry_run:
        print("\n[DRY-RUN] No changes made.")
        return

    # Create the channel
    new_ch = db.add_channel(
        name=name,
        chat_id=chat_id,
        discord_webhook=webhook,
    )
    new_id = new_ch["id"]
    print(f"\n  ✓ Channel created with ID: {new_id}")

    # Apply AI config from template
    update_kwargs = {
        "ai_enabled": template_key != "none",
        "discord_role_id": role_id,
    }

    if source:
        update_kwargs.update({
            "ai_provider":          source.get("ai_provider"),
            "ai_model":             source.get("ai_model"),
            "ai_fallback_provider": source.get("ai_fallback_provider"),
            "ai_fallback_model":    source.get("ai_fallback_model"),
            "ai_triage_prompt":     source.get("ai_triage_prompt"),
            "ai_format_prompt":     source.get("ai_format_prompt"),
        })

    db.update_channel(new_id, **update_kwargs)
    print(f"  ✓ AI config applied from template '{TEMPLATES[template_key]['description']}'")

    if role_id:
        print(f"  ✓ Discord role ID set: {role_id}")

    # Final verification
    channels = db.get_channels(enabled_only=False)
    verified = next((ch for ch in channels if ch["id"] == new_id), None)

    print()
    print("─" * 60)
    print("✅ CHANNEL ADDED SUCCESSFULLY")
    print("─" * 60)
    print(f"  ID:              {verified['id']}")
    print(f"  Name:            {verified['name']}")
    print(f"  Chat ID:         {verified['chat_id']}")
    print(f"  AI Enabled:      {verified['ai_enabled']}")
    print(f"  Primary AI:      {verified.get('ai_provider') or '(global/Grok)'}")
    print(f"  Fallback AI:     {verified.get('ai_fallback_provider')}/{verified.get('ai_fallback_model')}")
    print(f"  Discord Role:    {verified['discord_role_id'] or '(none)'}")
    print(f"  Triage Prompt:   {'SET' if verified.get('ai_triage_prompt') else 'NOT SET'}")
    print(f"  Format Prompt:   {'SET' if verified.get('ai_format_prompt') else 'NOT SET'}")
    print("─" * 60)
    print()
    print("⚡ Restart the bot on App Platform to start forwarding from this channel.")
    print()


def interactive_mode():
    """Prompt the user for channel details interactively."""
    print()
    print("═" * 60)
    print("  ADD NEW TELEGRAM → DISCORD CHANNEL")
    print("═" * 60)

    # Show existing channels for reference
    print("\nExisting channels:")
    list_existing_channels()

    # Gather inputs
    name = input("Channel name: ").strip()
    if not name:
        print("✗  Name is required.")
        sys.exit(1)

    chat_id = input("Telegram Chat ID (e.g. -1001234567890): ").strip()
    if not chat_id:
        print("✗  Chat ID is required.")
        sys.exit(1)

    webhook = input("Discord Webhook URL: ").strip()
    if not webhook:
        print("✗  Discord Webhook is required.")
        sys.exit(1)

    # Template selection
    print()
    print("AI Templates:")
    for key, val in TEMPLATES.items():
        print(f"  {key:<8} → {val['description']}")
    template_key = input("\nTemplate [t2t]: ").strip().lower() or "t2t"
    if template_key not in TEMPLATES:
        print(f"✗  Unknown template '{template_key}'. Choose from: {', '.join(TEMPLATES.keys())}")
        sys.exit(1)

    # Role ID
    print()
    print("Known role IDs:")
    for key, rid in KNOWN_ROLES.items():
        print(f"  {key:<8} → {rid}")
    role_input = input("\nDiscord Role ID (or name from above, or leave blank): ").strip()
    role_id = KNOWN_ROLES.get(role_input, role_input) if role_input else None

    print()
    add_channel(name=name, chat_id=chat_id, webhook=webhook, template_key=template_key, role_id=role_id)


# ─────────────────────────────────────────────────────────────────────────────
# CLI entry point
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    if not os.environ.get("BACKUP_DB_ADMIN_URL"):
        print("✗  BACKUP_DB_ADMIN_URL environment variable is not set.")
        sys.exit(1)

    parser = argparse.ArgumentParser(
        description="Add a new Telegram→Discord forwarding channel.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode (prompts for all inputs):
  python add_channel.py

  # Non-interactive with T2T Gold template:
  python add_channel.py --name "My Forex" --chat-id "-1001234567890" \\
      --webhook "https://discord.com/api/webhooks/..." --template t2t --role forex

  # SPX Options template, no role:
  python add_channel.py --name "SPX Signals" --chat-id "-1009876543210" \\
      --webhook "https://discord.com/api/webhooks/..." --template spx

  # Preview without making changes:
  python add_channel.py --name "Test" --chat-id "-1001111111111" \\
      --webhook "https://..." --dry-run

  # List existing channels:
  python add_channel.py --list
        """
    )
    parser.add_argument("--name",      help="Channel name")
    parser.add_argument("--chat-id",   help="Telegram chat ID (e.g. -1001234567890)")
    parser.add_argument("--webhook",   help="Discord webhook URL")
    parser.add_argument("--template",  default="t2t", choices=list(TEMPLATES.keys()),
                        help="AI config template to copy (default: t2t)")
    parser.add_argument("--role",      help=f"Discord role ID or name ({', '.join(KNOWN_ROLES.keys())})")
    parser.add_argument("--dry-run",   action="store_true", help="Preview without making changes")
    parser.add_argument("--list",      action="store_true", help="List all existing channels and exit")

    args = parser.parse_args()

    if args.list:
        list_existing_channels()
        sys.exit(0)

    # If no required args provided, go interactive
    if not args.name and not args.chat_id and not args.webhook:
        interactive_mode()
    else:
        # Non-interactive — validate required args
        missing = [f for f, v in [("--name", args.name), ("--chat-id", args.chat_id), ("--webhook", args.webhook)] if not v]
        if missing:
            print(f"✗  Missing required arguments: {', '.join(missing)}")
            parser.print_help()
            sys.exit(1)

        role_id = KNOWN_ROLES.get(args.role, args.role) if args.role else None

        add_channel(
            name=args.name,
            chat_id=args.chat_id,
            webhook=args.webhook,
            template_key=args.template,
            role_id=role_id,
            dry_run=args.dry_run,
        )

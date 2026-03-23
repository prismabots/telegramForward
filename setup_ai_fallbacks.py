#!/usr/bin/env python3
"""
setup_ai_fallbacks.py — Configure AI fallback providers for all channels.

This script sets up sensible default fallback configurations based on primary provider:
  - Grok (xAI)    → Fallback to GLM or OpenAI
  - GLM (Zhipu)   → Fallback to OpenAI
  - OpenAI        → Fallback to GLM (if configured)

Usage:
    python setup_ai_fallbacks.py [--dry-run] [--reset]

Options:
    --dry-run   : Show what would be configured without making changes
    --reset     : Reset all fallback configs to None before applying defaults
"""

import os
import sys
import logging
import argparse

# Make sure db module is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import db

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Default fallback chains per provider
FALLBACK_CONFIG = {
    "grok": {
        "fallback_provider": "glm",
        "fallback_model": "glm-4.7-flashx",
    },
    "glm": {
        "fallback_provider": "openai",
        "fallback_model": "gpt-5-nano",
    },
    "openai": {
        "fallback_provider": "glm",
        "fallback_model": "glm-4.7-flashx",
    },
    "google": {
        "fallback_provider": "openai",
        "fallback_model": "gpt-5-nano",
    },
    "deepseek": {
        "fallback_provider": "openai",
        "fallback_model": "gpt-5-nano",
    },
    "sonar": {
        "fallback_provider": "openai",
        "fallback_model": "gpt-5-nano",
    },
}

# Global settings for fallback (used when channel has no specific provider set)
GLOBAL_FALLBACK_CONFIG = {
    "fallback_provider": "glm",
    "fallback_model": "glm-4.7-flashx",
}


def configure_channel_fallbacks(dry_run: bool = False, reset: bool = False):
    """Configure fallback providers for all AI-enabled channels."""
    
    if not os.environ.get("BACKUP_DB_ADMIN_URL"):
        logger.error("BACKUP_DB_ADMIN_URL environment variable is not set.")
        sys.exit(1)

    logger.info("Initialising database schema...")
    db.init_db()

    logger.info("Loading channels from database...")
    channels = db.get_channels(enabled_only=False)

    if not channels:
        logger.error("No channels found in the database.")
        return

    logger.info(f"Found {len(channels)} channels")
    
    updated_count = 0
    skipped_count = 0

    for ch in channels:
        channel_id = ch["id"]
        channel_name = ch["name"]
        is_ai_enabled = ch.get("ai_enabled", False)
        primary_provider = ch.get("ai_provider")
        primary_model = ch.get("ai_model")

        if not is_ai_enabled:
            logger.info(f"⊘ '{channel_name}' (ID {channel_id}): AI not enabled, skipping")
            skipped_count += 1
            continue

        if not primary_provider:
            # Use global provider default
            fallback_cfg = GLOBAL_FALLBACK_CONFIG
            logger.info(
                f"⚙ '{channel_name}' (ID {channel_id}): No channel-specific provider, "
                f"using global defaults"
            )
        else:
            # Use provider-specific fallback
            fallback_cfg = FALLBACK_CONFIG.get(primary_provider, {})
            if not fallback_cfg:
                logger.warning(
                    f"⚠ '{channel_name}' (ID {channel_id}): Unknown provider '{primary_provider}', "
                    f"skipping"
                )
                skipped_count += 1
                continue
            logger.info(
                f"⚙ '{channel_name}' (ID {channel_id}): Provider='{primary_provider}', "
                f"setting fallback={fallback_cfg['fallback_provider']}"
            )

        if reset:
            if not dry_run:
                db.update_channel(
                    channel_id,
                    ai_fallback_provider=None,
                    ai_fallback_model=None,
                )
                logger.info(f"  → Reset fallback config")

        # Update channel with fallback config
        if dry_run:
            logger.info(
                f"  [DRY-RUN] Would set: ai_fallback_provider='{fallback_cfg.get('fallback_provider')}', "
                f"ai_fallback_model='{fallback_cfg.get('fallback_model')}'"
            )
        else:
            db.update_channel(
                channel_id,
                ai_fallback_provider=fallback_cfg.get("fallback_provider"),
                ai_fallback_model=fallback_cfg.get("fallback_model"),
            )
            logger.info(
                f"  → Updated: fallback_provider='{fallback_cfg.get('fallback_provider')}', "
                f"fallback_model='{fallback_cfg.get('fallback_model')}'"
            )

        updated_count += 1

    logger.info(f"\n✓ Summary: {updated_count} channels updated, {skipped_count} skipped")
    
    if dry_run:
        logger.info("(No changes were made — this was a DRY-RUN)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Configure AI fallback providers for channels.")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be configured without making changes")
    parser.add_argument("--reset", action="store_true", help="Reset all fallback configs to None before applying defaults")
    
    args = parser.parse_args()
    
    configure_channel_fallbacks(dry_run=args.dry_run, reset=args.reset)

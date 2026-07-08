"""
test_discord_embeds.py — Unit tests for Discord embed building.

These tests do not require a database or AI keys. They verify that
`discord_embeds.build_embed()` and `discord_embeds.create_webhook_payload()`
always produce embeds that Discord will accept.

Usage:
    python test_discord_embeds.py
"""

import sys
import os

# Ensure imports work when running from the repo root
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import discord_embeds


def _embed_has_content(embed: dict) -> bool:
    """Return True if the embed has a non-empty title or description."""
    title = embed.get("title")
    description = embed.get("description")
    return bool(
        (isinstance(title, str) and title.strip())
        or (isinstance(description, str) and description.strip())
    )


def test_empty_string():
    embed = discord_embeds.build_embed("")
    assert _embed_has_content(embed), "Empty string input must produce embed with content"
    assert embed.get("description") == "📷", "Empty input should use image placeholder"
    print("[PASS] test_empty_string passed")


def test_whitespace_only():
    for text in ["   ", "\n\n", " \t \n "]:
        embed = discord_embeds.build_embed(text)
        assert _embed_has_content(embed), f"Whitespace input {text!r} must produce embed with content"
    print("[PASS] test_whitespace_only passed")


def test_image_only_placeholder():
    payload = discord_embeds.create_webhook_payload(
        message_text="",
        role_id="1480307797261287714",
        username="Prisma Signals",
    )
    embeds = payload.get("embeds", [])
    assert len(embeds) == 1, "Payload must contain exactly one embed"
    embed = embeds[0]
    assert _embed_has_content(embed), "Image-only payload must have non-empty title or description"
    assert "description" in embed, "Image-only embed must have a description"
    assert embed["description"].strip(), "Image-only embed description must not be empty/whitespace"
    print("[PASS] test_image_only_placeholder passed")


def test_sanitizer_safety_net():
    # Simulate an embed that somehow lost both title and description after parsing.
    raw_embed = {"color": discord_embeds.COLOR_GRAY, "fields": []}
    sanitized = discord_embeds._sanitize_embed_for_discord(raw_embed)
    assert _embed_has_content(sanitized), "Sanitizer must add placeholder when title and description are missing"
    assert sanitized.get("description") == "Keep Alive / Status Update"
    print("[PASS] test_sanitizer_safety_net passed")


def test_normal_trading_signal():
    text = (
        "💎 **BUY EURUSD**\n"
        "🛒 Entry: 1.0850\n"
        "🎯 TP: 1.0900\n"
        "🚫 SL: 1.0800\n"
        "⏰ Timeframe: 1H"
    )
    embed = discord_embeds.build_embed(text)
    assert _embed_has_content(embed), "Normal signal must have content"
    assert "BUY EURUSD" in (embed.get("title") or "")
    assert len(embed.get("fields", [])) >= 3, "Normal signal should have multiple fields"
    print("[PASS] test_normal_trading_signal passed")


def test_long_description_truncated():
    long_text = "Entry: 1.0850\n" + ("A" * 5000)
    payload = discord_embeds.create_webhook_payload(
        message_text=long_text,
        username="Prisma Signals",
    )
    embed = payload["embeds"][0]
    description = embed.get("description", "")
    assert description, "Long description should not be empty"
    assert len(description) <= 4096, "Description must be within Discord limit"
    print("[PASS] test_long_description_truncated passed")


def test_long_title_truncated():
    long_title = "BUY " + "X" * 300
    payload = discord_embeds.create_webhook_payload(
        message_text=f"**{long_title}**\nEntry: 1.0",
        username="Prisma Signals",
    )
    embed = payload["embeds"][0]
    title = embed.get("title", "")
    assert title, "Long title should not be empty"
    assert len(title) <= 256, "Title must be within Discord limit"
    print("[PASS] test_long_title_truncated passed")


def test_empty_fields_array_is_fine():
    # Discord accepts empty fields as long as there is title/description.
    embed = discord_embeds.build_embed("Just a plain message")
    assert _embed_has_content(embed), "Plain message must have content"
    assert embed.get("fields", []) == [], "Plain message should have empty fields"
    print("[PASS] test_empty_fields_array_is_fine passed")


def test_create_webhook_payload_no_empty_description():
    payload = discord_embeds.create_webhook_payload(
        message_text="",
        role_id="123456789",
        username="Prisma Signals",
    )
    embed = payload["embeds"][0]
    # Discord rejects empty-string description; ensure it is either absent or non-empty.
    description = embed.get("description")
    assert description is None or description.strip(), "Payload must not contain empty description"
    assert _embed_has_content(embed), "Payload embed must have title or description"
    print("[PASS] test_create_webhook_payload_no_empty_description passed")


def run_all_tests():
    tests = [
        test_empty_string,
        test_whitespace_only,
        test_image_only_placeholder,
        test_sanitizer_safety_net,
        test_normal_trading_signal,
        test_long_description_truncated,
        test_long_title_truncated,
        test_empty_fields_array_is_fine,
        test_create_webhook_payload_no_empty_description,
    ]

    failed = 0
    for test in tests:
        try:
            test()
        except AssertionError as e:
            print(f"[FAIL] {test.__name__} failed: {e}")
            failed += 1
        except Exception as e:
            print(f"[ERROR] {test.__name__} raised {type(e).__name__}: {e}")
            failed += 1

    print()
    if failed == 0:
        print(f"[OK] All {len(tests)} discord_embeds tests passed!")
        return 0
    else:
        print(f"[WARN] {failed}/{len(tests)} tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())

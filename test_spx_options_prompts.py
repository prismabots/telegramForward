"""
test_spx_options_prompts.py — Test SPX Options AI prompts

This script tests the triage and format prompts for channel 13 (SPX Options)
against various input scenarios to ensure they handle:
- Arabic and English content
- Options terminology (Call/Put)
- Promotional content filtering
- Edge cases (image-only, meaningless content)

Usage:
    python test_spx_options_prompts.py
"""

import os
import sys
import asyncio
import json
import db
from ai_services import triage_message

# Load prompts
PROMPTS_DIR = os.path.join(os.path.dirname(__file__), "prompts")

with open(os.path.join(PROMPTS_DIR, "triage_spx_options.txt"), "r", encoding="utf-8") as f:
    TRIAGE_PROMPT = f.read().strip()

with open(os.path.join(PROMPTS_DIR, "format_spx_options.txt"), "r", encoding="utf-8") as f:
    FORMAT_PROMPT = f.read().strip()

# Test cases
TEST_CASES = [
    {
        "name": "Valid SPX Call in Arabic",
        "input": "كول SPX 5800 شراء الآن، الهدف 5850",
        "expect_action": "forward"
    },
    {
        "name": "Valid SPX Put with levels",
        "input": "SPX 5850 Put - Price reached resistance at 5875, consider exit. Support at 5820.",
        "expect_action": "forward"
    },
    {
        "name": "Promotional content",
        "input": "🔥 Join our premium signals service! Get exclusive access to VIP channel. Limited time offer! Click here to buy now.",
        "expect_action": "discard"
    },
    {
        "name": "Mixed - Valid signal with promo",
        "input": "SPX Call 5800 entered. Target 5850. 🎯 Join VIP for more signals!",
        "expect_action": "forward"  # Should forward but remove promo in format stage
    },
    {
        "name": "Arabic Put signal",
        "input": "بوت SPX 5900 السعر عند المقاومة",
        "expect_action": "forward"
    },
    {
        "name": "Just engagement request",
        "input": "Don't forget to like and subscribe! Share with your friends!",
        "expect_action": "discard"
    },
    {
        "name": "Image only placeholder",
        "input": "[Image only - no text]",
        "expect_action": "forward"  # Will output "------------" in format
    },
    {
        "name": "Generic market comment",
        "input": "Market looking strong today! Great opportunities ahead.",
        "expect_action": "discard"
    },
    {
        "name": "SPX with gains/losses",
        "input": "SPX Call 5750 closed +$450 profit. Price moved as expected.",
        "expect_action": "forward"
    },
    {
        "name": "Store/product link",
        "input": "Check out our new indicator for only $99! Best trading tool ever. Link in bio.",
        "expect_action": "discard"
    }
]


async def test_triage():
    """Test the triage prompt with all test cases."""
    print("\n" + "=" * 70)
    print("TESTING TRIAGE PROMPT")
    print("=" * 70)
    
    # Get AI settings from database
    settings = db.get_all_settings()
    provider = settings.get("ai_provider", "openai")
    model = settings.get("ai_model", "gpt-4o-mini")
    api_key = settings.get("ai_api_key", "")
    
    if not api_key:
        print("❌ ERROR: No AI API key found in database")
        return 0, len(TEST_CASES)
    
    passed = 0
    failed = 0
    
    for i, test in enumerate(TEST_CASES, 1):
        print(f"\n[Test {i}/{len(TEST_CASES)}] {test['name']}")
        print(f"Input: {test['input'][:100]}...")
        
        try:
            # Use triage_message function
            result = await triage_message(
                message_text=test['input'],
                channel_name="Test Channel 13",
                triage_prompt=TRIAGE_PROMPT,
                format_prompt=FORMAT_PROMPT,
                provider=provider,
                model=model,
                api_key=api_key,
                is_reply=False,
                channel_id=13,
                verbose_logging=False
            )
            
            action = result.action.lower()
            reason = result.reason
            
            print(f"Response: {action} - {reason}")
            
            # Check if matches expectation
            if action == test['expect_action']:
                print("✅ PASS")
                passed += 1
            else:
                print(f"❌ FAIL - Expected '{test['expect_action']}', got '{action}'")
                failed += 1
                
        except Exception as e:
            print(f"❌ ERROR: {e}")
            failed += 1
    
    print("\n" + "=" * 70)
    print(f"TRIAGE TEST RESULTS: {passed} passed, {failed} failed out of {len(TEST_CASES)}")
    print("=" * 70)
    
    return passed, failed


async def test_format():
    """Test the format prompt with sample inputs."""
    print("\n" + "=" * 70)
    print("TESTING FORMAT PROMPT")
    print("=" * 70)
    
    # Get AI settings from database
    settings = db.get_all_settings()
    provider = settings.get("ai_provider", "openai")
    model = settings.get("ai_model", "gpt-4o-mini")
    api_key = settings.get("ai_api_key", "")
    
    if not api_key:
        print("❌ ERROR: No AI API key found in database")
        return
    
    format_tests = [
        {
            "name": "Arabic Call signal",
            "input": "كول SPX 5800 شراء الآن، الهدف 5850",
        },
        {
            "name": "Signal with promotional text",
            "input": "SPX Call 5800 entered. Target 5850. 🎯\n\n🔥 Join our VIP channel for more signals! Limited time offer!",
        },
        {
            "name": "Image only",
            "input": "[Image only - no text]",
        },
        {
            "name": "Put with resistance/support",
            "input": "SPX 5850 Put - Price reached resistance at 5875. Support at 5820. Consider exit near resistance.",
        }
    ]
    
    for i, test in enumerate(format_tests, 1):
        print(f"\n[Test {i}/{len(format_tests)}] {test['name']}")
        print(f"Input:\n{test['input']}")
        
        try:
            # Use triage_message to test both triage and format
            result = await triage_message(
                message_text=test['input'],
                channel_name="Test Channel 13",
                triage_prompt=TRIAGE_PROMPT,
                format_prompt=FORMAT_PROMPT,
                provider=provider,
                model=model,
                api_key=api_key,
                is_reply=False,
                channel_id=13,
                verbose_logging=False
            )
            
            if result.action == "discard":
                print(f"\n⚠️  Message would be discarded: {result.reason}")
            else:
                formatted = result.rewritten_text or test['input']
                print(f"\nFormatted Output:\n{formatted}")
            print("-" * 70)
            
        except Exception as e:
            print(f"❌ ERROR: {e}")
    
    print("\n" + "=" * 70)
    print("FORMAT TEST COMPLETE")
    print("=" * 70)


async def main():
    """Run all tests."""
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 15 + "SPX OPTIONS AI PROMPT TESTING" + " " * 24 + "║")
    print("╚" + "═" * 68 + "╝")
    
    # Check environment
    if not os.environ.get("BACKUP_DB_ADMIN_URL"):
        print("\n⚠️  WARNING: BACKUP_DB_ADMIN_URL not set")
        print("   Some tests may fail without database access")
    
    # Run triage tests
    await test_triage()
    
    # Run format tests
    await test_format()
    
    print("\n✅ All tests complete!\n")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        sys.exit(1)

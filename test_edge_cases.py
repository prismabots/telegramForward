"""
test_edge_cases.py — Test edge cases: images, empty messages, minimal content

Usage:
    python test_edge_cases.py
"""

import os
import sys
import asyncio
import db
from ai_services import triage_message

# Load prompts
PROMPTS_DIR = os.path.join(os.path.dirname(__file__), "prompts")

with open(os.path.join(PROMPTS_DIR, "triage_spx_options.txt"), "r", encoding="utf-8") as f:
    TRIAGE_PROMPT = f.read().strip()

with open(os.path.join(PROMPTS_DIR, "format_spx_options.txt"), "r", encoding="utf-8") as f:
    FORMAT_PROMPT = f.read().strip()


EDGE_CASES = [
    {
        "name": "Empty string",
        "text": "",
        "expected": "System should handle gracefully"
    },
    {
        "name": "Just whitespace",
        "text": "   \n\n   ",
        "expected": "Should be treated as empty"
    },
    {
        "name": "Image only marker",
        "text": "[Image]",
        "expected": "Should output ------------"
    },
    {
        "name": "Photo only marker",
        "text": "[Photo]",
        "expected": "Should output ------------"
    },
    {
        "name": "Channel name only",
        "text": "SPX | كنترول الاوبشن",
        "expected": "Should discard - no trading data"
    },
    {
        "name": "Just emojis",
        "text": "🔥🔥🔥",
        "expected": "Should discard - no trading data"
    },
    {
        "name": "Greeting only",
        "text": "مساء الخير",
        "expected": "Should discard - greeting, no trading data"
    },
    {
        "name": "Question without signal",
        "text": "ماذا عن السوق اليوم؟",
        "expected": "Should discard - question, no signal"
    },
    {
        "name": "Very minimal signal",
        "text": "6850 Call",
        "expected": "Should forward - has symbol and type"
    },
    {
        "name": "Just a number",
        "text": "6850",
        "expected": "Should discard - number alone isn't a signal"
    },
]


async def test_edge_cases():
    """Test edge cases and minimal content."""
    
    print("\n" + "=" * 80)
    print("TESTING EDGE CASES - SPX OPTIONS AI")
    print("=" * 80)
    
    # Get AI settings
    try:
        settings = db.get_all_settings()
        provider = settings.get("ai_provider", "openai")
        model = settings.get("ai_model", "gpt-4o-mini")
        api_key = settings.get("ai_api_key", "") or os.environ.get("OPENAI_API_KEY", "")
        
        if not api_key:
            print("❌ ERROR: No AI API key found")
            return
            
    except Exception as e:
        print(f"❌ ERROR: Could not connect to database: {e}")
        return
    
    print(f"\n📋 Testing {len(EDGE_CASES)} edge cases...\n")
    
    results = {"passed": 0, "failed": 0, "skipped": 0}
    
    for i, test in enumerate(EDGE_CASES, 1):
        print("─" * 80)
        print(f"[Test {i}/{len(EDGE_CASES)}] {test['name']}")
        print("─" * 80)
        print(f"📨 INPUT: '{test['text']}'")
        print(f"🎯 EXPECTED: {test['expected']}")
        
        # Special handling for empty/whitespace
        if not test['text'].strip():
            print("✅ SKIPPED: Empty message handled by system before AI")
            results["skipped"] += 1
            print()
            continue
        
        try:
            result = await triage_message(
                message_text=test['text'],
                channel_name="Control Optional SPX (Edge Test)",
                triage_prompt=TRIAGE_PROMPT,
                format_prompt=FORMAT_PROMPT,
                provider=provider,
                model=model,
                api_key=api_key,
                is_reply=False,
                channel_id=13,
                verbose_logging=False
            )
            
            print(f"✅ RESULT: {result.action.upper()}")
            print(f"   Reason: {result.reason}")
            
            if result.action == "forward" and result.rewritten_text:
                print(f"📝 OUTPUT:\n{result.rewritten_text}")
            elif result.action == "discard":
                print(f"🚫 DISCARDED")
            
            results["passed"] += 1
            
        except Exception as e:
            print(f"❌ ERROR: {e}")
            results["failed"] += 1
        
        print()
    
    print("=" * 80)
    print(f"EDGE CASE TEST RESULTS:")
    print(f"  Passed:  {results['passed']}")
    print(f"  Failed:  {results['failed']}")
    print(f"  Skipped: {results['skipped']}")
    print(f"  Total:   {len(EDGE_CASES)}")
    print("=" * 80)


async def main():
    print("\n╔" + "═" * 78 + "╗")
    print("║" + " " * 22 + "EDGE CASE TESTING - CHANNEL 13" + " " * 26 + "║")
    print("╚" + "═" * 78 + "╝")
    
    if not os.environ.get("BACKUP_DB_ADMIN_URL"):
        print("\n❌ ERROR: BACKUP_DB_ADMIN_URL environment variable not set")
        sys.exit(1)
    
    await test_edge_cases()
    
    print("\n💡 All edge cases tested!\n")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️  Tests interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)

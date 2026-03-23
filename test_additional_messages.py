"""
test_additional_messages.py — Test more real messages from Channel 13

Usage:
    python test_additional_messages.py
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


# Additional real message examples from new screenshots
TEST_MESSAGES = [
    {
        "name": "Screenshot 5: Put with status update",
        "text": """SPX | كنترول الاوبشن

SPXW $6,685
10 Mar 26 (W) Put 100

3.15
▼-6.73 -68.12%

Mid: 3.10
Open Int: 812
Vol: 6,015

دخول بوت

6685

وقفك""",
        "expected": "Should forward - Put signal with entry and stop notice",
        "notes": "Contains 'دخول بوت' (enter Put) and 'وقفك' (your stop/wait)"
    },
    {
        "name": "Screenshot 6: Call with chart analysis",
        "text": """SPX | كنترول الاوبشن
SPX | كنترول الاوبشن
1.50   وقفك   6850   عقد كول

SPXW $6,850
10 Mar 26 (W) Call 100

4.20
▼-4.10 -49.40%

Mid: 4.25
Open Int: 3,872
Vol: 76,532

SPX 6,834.13 +0.56%
Open: 20:07 03/10 MSK ⚡

Chart Calculator

VWAP 3.08

4.83        +4.90        +109.86%
4.90""",
        "expected": "Should forward - Call signal with contract details and chart",
        "notes": "Contains 'عقد كول' (Call contract) with price 6850 and analysis"
    },
    {
        "name": "Simple Put entry with price",
        "text": """دخول بوت 6685""",
        "expected": "Should forward - Simple Put entry",
        "notes": "Very short format: enter Put at 6685"
    },
    {
        "name": "Call with stop price",
        "text": """عقد كول 6850 وقفك 1.50""",
        "expected": "Should forward - Call with stop level",
        "notes": "Call contract at 6850, stop at 1.50"
    },
    {
        "name": "Status update only",
        "text": """وقفك""",
        "expected": "Should discard - Just 'your stop/wait' with no context",
        "notes": "No trading data, just status word"
    },
    {
        "name": "Mixed: Signal + reactions note",
        "text": """SPX Put 6685
دخول الآن
السعر 3.15

شكراً لتفاعلكم""",
        "expected": "Should forward but remove 'thanks for interaction' part",
        "notes": "Valid signal followed by engagement text"
    },
]


async def test_additional_messages():
    """Test the AI system with additional real messages."""
    
    print("\n" + "=" * 80)
    print("TESTING ADDITIONAL SPX OPTIONS MESSAGES")
    print("=" * 80)
    
    # Get AI settings from database with environment variable fallback
    try:
        settings = db.get_all_settings()
        provider = settings.get("ai_provider", "openai")
        model = settings.get("ai_model", "gpt-4o-mini")
        
        # Fall back to environment variable if not in database
        api_key = settings.get("ai_api_key", "") or os.environ.get("OPENAI_API_KEY", "")
        
        if not api_key:
            print("❌ ERROR: No AI API key found")
            print("   Not in database (ai_api_key) and not in environment (OPENAI_API_KEY)")
            print("   Please set: $env:OPENAI_API_KEY = 'your-key-here'")
            return
            
    except Exception as e:
        print(f"❌ ERROR: Could not connect to database: {e}")
        print("   Make sure BACKUP_DB_ADMIN_URL is set")
        return
    
    print(f"\n📋 AI Configuration:")
    print(f"   Provider: {provider}")
    print(f"   Model: {model}")
    print(f"   API Key: {'*' * 20}{api_key[-4:] if len(api_key) > 4 else '****'}")
    
    # Test each message
    passed = 0
    failed = 0
    
    for i, test in enumerate(TEST_MESSAGES, 1):
        print("\n" + "─" * 80)
        print(f"[Test {i}/{len(TEST_MESSAGES)}] {test['name']}")
        print("─" * 80)
        print(f"\n📨 INPUT MESSAGE:")
        print(test['text'])
        print(f"\n🎯 EXPECTED: {test['expected']}")
        print(f"💡 NOTES: {test['notes']}")
        
        try:
            result = await triage_message(
                message_text=test['text'],
                channel_name="Control Optional SPX (Test)",
                triage_prompt=TRIAGE_PROMPT,
                format_prompt=FORMAT_PROMPT,
                provider=provider,
                model=model,
                api_key=api_key,
                is_reply=False,
                channel_id=13,
                verbose_logging=False
            )
            
            print(f"\n✅ TRIAGE RESULT: {result.action.upper()}")
            print(f"   Reason: {result.reason}")
            
            if result.action == "forward":
                if result.rewritten_text:
                    print(f"\n📝 FORMATTED OUTPUT:")
                    print("─" * 40)
                    print(result.rewritten_text)
                    print("─" * 40)
                    passed += 1
                else:
                    print(f"\n📝 FORMATTED OUTPUT: (original text, no rewrite)")
                    passed += 1
            else:
                print(f"\n🚫 MESSAGE DISCARDED")
                passed += 1
                
        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            failed += 1
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 80)
    print(f"TEST RESULTS: {passed} passed, {failed} failed out of {len(TEST_MESSAGES)}")
    print("=" * 80)


async def main():
    """Run the test suite."""
    
    print("\n")
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 18 + "ADDITIONAL MESSAGE TESTING - CHANNEL 13" + " " * 21 + "║")
    print("╚" + "═" * 78 + "╝")
    
    # Check environment
    if not os.environ.get("BACKUP_DB_ADMIN_URL"):
        print("\n❌ ERROR: BACKUP_DB_ADMIN_URL environment variable not set")
        print("   Set it with: $env:BACKUP_DB_ADMIN_URL = 'postgresql://...'")
        sys.exit(1)
    
    await test_additional_messages()
    
    print("\n💡 TIP: Review the outputs to ensure they meet your requirements")
    print("   If adjustments are needed, edit the prompt files and reapply\n")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

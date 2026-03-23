"""
test_real_messages.py — Test SPX Options AI with real message examples

This script tests the AI system with actual message content from Channel 13
to validate triage and formatting behavior.

Usage:
    python test_real_messages.py
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


# Real message examples from screenshots
REAL_MESSAGES = [
    {
        "name": "Screenshot 1: SPX Put with Arabic",
        "text": """SPX | كنترول الاوبشن
SPXW $6,805
10 Mar 26 (W) Put 100

2.85
▼-41.49 -93.57%

Mid: 2.88
Open Int: 261
Vol: 30,645

بوت خطير و سريع

6805""",
        "expected": "Should forward - valid Put signal with strike price"
    },
    {
        "name": "Screenshot 2: Engagement request",
        "text": """SPX | كنترول الاوبشن

استفدت من الطرح تفاعلك 🔥""",
        "expected": "Should DISCARD - engagement request, no trading data"
    },
    {
        "name": "Screenshot 3: Call with profit info",
        "text": """SPX | كنترول الاوبشن
SPX | كنترول الاوبشن
6840  دخول كول

SPXW $6,840
10 Mar 26 (W) Call 100

10.00
▼-0.81 -7.49%

Mid: 9.95
Open Int: 1,310
Vol: 65,246

SPX 6,840.54 +0.66%
Open: 20:33 03/10 MSK ⚡

Chart Calculator

VWAP 5.65

13.64        -13.86        +116.52%
13.86

ربحنا فيه فوق

1000$ ( 3750 ريال )""",
        "expected": "Should forward - valid Call signal with entry and profit info"
    },
    {
        "name": "Screenshot 4: Chart with technical levels",
        "text": """SPX | كنترول الاوبشن
SPX | كntrول الاوبشن
Photo

[Trading chart with support/resistance levels visible:
- Multiple levels marked: 6975.5, 6881.8, 6830.4, 6744.9, 6773.5, 6659.4, 6547.1
- Chart shows price action and technical analysis]""",
        "expected": "Should forward - contains technical analysis levels"
    },
    {
        "name": "Simple Put entry",
        "text": """بوت 6805 دخول الان""",
        "expected": "Should forward - Put entry signal"
    },
    {
        "name": "Call entry with target",
        "text": """كول 6840
الهدف 6900""",
        "expected": "Should forward - Call with target"
    },
]


async def test_real_messages():
    """Test the AI system with real messages from Channel 13."""
    
    print("\n" + "=" * 80)
    print("TESTING SPX OPTIONS AI WITH REAL MESSAGES")
    print("=" * 80)
    
    # Get AI settings from database with environment variable fallback (like main.py does)
    try:
        settings = db.get_all_settings()
        provider = settings.get("ai_provider", "openai")
        model = settings.get("ai_model", "gpt-4o-mini")
        
        # Fall back to environment variable if not in database (same as main.py)
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
    for i, test in enumerate(REAL_MESSAGES, 1):
        print("\n" + "─" * 80)
        print(f"[Test {i}/{len(REAL_MESSAGES)}] {test['name']}")
        print("─" * 80)
        print(f"\n📨 INPUT MESSAGE:")
        print(test['text'][:200] + "..." if len(test['text']) > 200 else test['text'])
        print(f"\n🎯 EXPECTED: {test['expected']}")
        
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
                else:
                    print(f"\n📝 FORMATTED OUTPUT: (original text, no rewrite)")
            else:
                print(f"\n🚫 MESSAGE DISCARDED")
                
        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("✅ ALL TESTS COMPLETE")
    print("=" * 80)


async def main():
    """Run the test suite."""
    
    print("\n")
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 20 + "REAL MESSAGE TESTING - CHANNEL 13" + " " * 25 + "║")
    print("╚" + "═" * 78 + "╝")
    
    # Check environment
    if not os.environ.get("BACKUP_DB_ADMIN_URL"):
        print("\n❌ ERROR: BACKUP_DB_ADMIN_URL environment variable not set")
        print("   Set it with: $env:BACKUP_DB_ADMIN_URL = 'postgresql://...'")
        sys.exit(1)
    
    await test_real_messages()
    
    print("\n💡 TIP: Review the formatted outputs to ensure they meet your requirements")
    print("   If adjustments are needed, edit the prompt files and rerun this test\n")


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

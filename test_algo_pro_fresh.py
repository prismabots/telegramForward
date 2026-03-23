"""
test_algo_pro_fresh.py — Test Algo Pro AI with fresh screenshots

Usage:
    python test_algo_pro_fresh.py
"""

import os
import sys
import asyncio
import db
from ai_services import triage_message

# Load prompts
PROMPTS_DIR = os.path.join(os.path.dirname(__file__), "prompts")

with open(os.path.join(PROMPTS_DIR, "triage_algo_pro.txt"), "r", encoding="utf-8") as f:
    TRIAGE_PROMPT = f.read().strip()

with open(os.path.join(PROMPTS_DIR, "format_algo_pro.txt"), "r", encoding="utf-8") as f:
    FORMAT_PROMPT = f.read().strip()


# Fresh messages from new screenshots
FRESH_MESSAGES = [
    {
        "name": "Screenshot 1: $QQQ trade idea",
        "text": """$QQQ likely to dip and rip upwards at market open

BM""",
        "expected": "Should forward - trade idea with symbol, remove BM"
    },
    {
        "name": "Screenshot 2: $QQQ with meme GIF",
        "text": """$QQQ likely to dip and rip upwa...
[GIF: Person looking anxious/waiting]""",
        "expected": "Should forward - has trading context with GIF"
    },
    {
        "name": "Screenshot 3: $QQQ with user reply",
        "text": """$QQQ likely to dip and rip upwards at market open  BM

MikeH 11:27 AM
QQQ 597 calls this morning in 1.75 out 3.17, thanks Brian! One runner left (edited)""",
        "expected": "Should forward - trade idea with user feedback, remove names"
    },
    {
        "name": "Screenshot 4: $CL gap fill analysis",
        "text": """Trade idea 💡☁️

$CL gap fill will likely cause price to reverse back upwards (92.55)

BM""",
        "expected": "Should forward - trade idea with price level, remove BM"
    },
    {
        "name": "Screenshot 5: $CL update with excitement",
        "text": """Trade idea 💡☁️  $CL gap fill will likely cause price to...
1 point gain in seconds!!! GHAND!

now 93.85""",
        "expected": "Should forward - trade update with results, keep excitement"
    },
    {
        "name": "Screenshot 6: RIVN chart (duplicate from before)",
        "text": """Trade idea 💡☁️  💬on RIVN for a quick pop (up) then dro...
[Chart showing RIVN pump and dump with arrows]
RIVN with the pump n dump""",
        "expected": "Should forward - chart with analysis"
    },
]


async def test_fresh_messages():
    """Test the AI system with fresh screenshots."""
    
    print("\n" + "=" * 80)
    print("TESTING ALGO PRO AI WITH FRESH SCREENSHOTS")
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
    
    print(f"\n📋 AI Configuration:")
    print(f"   Provider: {provider}")
    print(f"   Model: {model}")
    print(f"   Testing with fresh screenshots...\n")
    
    # Test each message
    passed = 0
    failed = 0
    
    for i, test in enumerate(FRESH_MESSAGES, 1):
        print("─" * 80)
        print(f"[Test {i}/{len(FRESH_MESSAGES)}] {test['name']}")
        print("─" * 80)
        print(f"\n📨 INPUT MESSAGE:")
        print(test['text'])
        print(f"\n🎯 EXPECTED: {test['expected']}")
        
        try:
            result = await triage_message(
                message_text=test['text'],
                channel_name="TradeAlgo Alerts (Fresh Test)",
                triage_prompt=TRIAGE_PROMPT,
                format_prompt=FORMAT_PROMPT,
                provider=provider,
                model=model,
                api_key=api_key,
                is_reply=False,
                channel_id=14,
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
                    
                    # Check if analyst names were removed
                    if "BM" in result.rewritten_text or "Brian" in result.rewritten_text:
                        print("⚠️  WARNING: Analyst name still present in output!")
                    else:
                        print("✓ Analyst names removed correctly")
                else:
                    print(f"\n📝 FORMATTED OUTPUT: (original text)")
                passed += 1
            else:
                print(f"\n🚫 MESSAGE DISCARDED")
                passed += 1
                
        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            failed += 1
            import traceback
            traceback.print_exc()
        
        print()
    
    print("=" * 80)
    print(f"FRESH TEST RESULTS: {passed} passed, {failed} failed out of {len(FRESH_MESSAGES)}")
    print("=" * 80)


async def main():
    """Run the test suite."""
    
    print("\n")
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 18 + "ALGO PRO FRESH SCREENSHOT TESTING" + " " * 27 + "║")
    print("╚" + "═" * 78 + "╝")
    
    # Check environment
    if not os.environ.get("BACKUP_DB_ADMIN_URL"):
        print("\n❌ ERROR: BACKUP_DB_ADMIN_URL environment variable not set")
        sys.exit(1)
    
    await test_fresh_messages()
    
    print("\n💡 Review the outputs - analyst names should be removed!\n")


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

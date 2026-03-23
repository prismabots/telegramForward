"""
test_algo_pro_messages.py — Test Algo Pro AI with real messages

Usage:
    python test_algo_pro_messages.py
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


# Real messages from screenshots
TEST_MESSAGES = [
    {
        "name": "Screenshot 1: Economic Calendar + Market Analysis",
        "text": """Hello traders and happy Tuesday! Attached is a screenshot of today's economic calendar. Notable times listed below in Eastern Time

8:45 AM — ADP Employment Change
10:00 AM — Existing Home Sales (Feb)

A fairly light day today, but the main focus is going to still be on the middle east and what might be developing in Iran. Again, I am focused on what the SPY Price Action than anything. If that is able to be used, oil prices should stay down. so that's where my focus will lie today. Also, as a reminder, I will be going live here at 9 ET in the "Live Trading Time" on the "Trade Algo" tab to start prepping for the day ahead. See you all there!

https://dashboard.tradealgo.com/market-analysis""",
        "expected": "Should forward - market analysis from analyst",
        "analyst": "Dane"
    },
    {
        "name": "Screenshot 2: Motivational Meme",
        "text": """TIME TO TRADE
GOOD MORNING!
[Image: cats with coffee cups]""",
        "expected": "Should DISCARD - pure motivational content, no trading data",
        "analyst": None
    },
    {
        "name": "Screenshot 3: Trade Idea RIVN",
        "text": """on RIVN for a quick pop (up) then drop (down) this morning

BM""",
        "expected": "Should forward - trade idea with symbol",
        "analyst": "BM"
    },
    {
        "name": "Screenshot 4: Futures Support Level",
        "text": """FUTURES $CL

70.95 -80.35 4hr support

BM""",
        "expected": "Should forward - futures level",
        "analyst": "BM"
    },
    {
        "name": "Screenshot 5: GIF with Trade Context",
        "text": """FUTURES $CL  70.95 -80.35 4hr support  BM
[GIF]""",
        "expected": "Should forward - has trading context",
        "analyst": "BM"
    },
    {
        "name": "Screenshot 6: Trade Update",
        "text": """lovely bounce up a buck! taking most to be safe!

BM""",
        "expected": "Should forward - trade update",
        "analyst": "BM"
    },
    {
        "name": "Screenshot 7: Profit Taking",
        "text": """FUTURES $CL  70.95 -80.35 4hr support  B...
$4 pump from entry, fantastic place to get out

Cheers""",
        "expected": "Should forward - profit update",
        "analyst": "BM"
    },
    {
        "name": "Screenshot 8: Chart Analysis",
        "text": """on RIVN for a quick pop (up) then dro...
[Chart image showing RIVN pump and dump]
RIVN with the pump n dump""",
        "expected": "Should forward - chart with analysis",
        "analyst": None
    },
]


async def test_algo_pro_messages():
    """Test the AI system with real Algo Pro messages."""
    
    print("\n" + "=" * 80)
    print("TESTING ALGO PRO AI WITH REAL MESSAGES")
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
    print(f"   API Key: {'*' * 20}{api_key[-4:] if len(api_key) > 4 else '****'}")
    
    # Test each message
    passed = 0
    failed = 0
    
    for i, test in enumerate(TEST_MESSAGES, 1):
        print("\n" + "─" * 80)
        print(f"[Test {i}/{len(TEST_MESSAGES)}] {test['name']}")
        if test['analyst']:
            print(f"Analyst: {test['analyst']}")
        print("─" * 80)
        print(f"\n📨 INPUT MESSAGE:")
        print(test['text'][:200] + "..." if len(test['text']) > 200 else test['text'])
        print(f"\n🎯 EXPECTED: {test['expected']}")
        
        try:
            result = await triage_message(
                message_text=test['text'],
                channel_name="TradeAlgo Alerts (Test)",
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
    print("║" + " " * 20 + "ALGO PRO MESSAGE TESTING - CHANNEL 14" + " " * 21 + "║")
    print("╚" + "═" * 78 + "╝")
    
    # Check environment
    if not os.environ.get("BACKUP_DB_ADMIN_URL"):
        print("\n❌ ERROR: BACKUP_DB_ADMIN_URL environment variable not set")
        sys.exit(1)
    
    await test_algo_pro_messages()
    
    print("\n💡 TIP: Review the outputs to ensure they meet your requirements\n")


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

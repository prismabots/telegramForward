"""
Test the FOREX/Gold AI triage and format prompts with sample messages.
"""
import asyncio
import sys
import os
sys.path.insert(0, '.')

from ai_services import triage_message

# Get AI provider settings from environment or use defaults
PROVIDER = os.getenv("AI_PROVIDER", "openai")
MODEL = os.getenv("AI_MODEL", "gpt-4o-mini")
API_KEY = os.getenv("OPENAI_API_KEY", "")

# Test samples from user
test_messages = [
    # Sample 1: Basic buy signal
    """T2T Gold Premium
Gold buy now 5158. Sl 5155 Tp 5180""",
    
    # Sample 2: Running signal with update
    """T2T Gold Premium
Gold buy now 5158. Sl 5155 Tp 5180

#GOLD Running 107+Pip's ✅ keep hold for massive Profit 💯
SL move to entry point""",
    
    # Sample 3: Closed signal with promotional text
    """Gold Closed +140 Pips 🔥🔥🔥
RR 4.6 ✅
Another Banger from the VIP Room 💰💰💰
Consistency is King 👑""",
    
    # Sample 4: Another closed signal
    """Gold Closed +247 Pips 🔥🔥🔥
RR 8.6 ✅
Another Banger from the VIP Room 💰💰💰
Consistency is King 👑""",
    
    # Sample 5: Sell signal from earlier
    """T2T Gold Premium
Gold sell @ 5169.70 ...
Sl @ 5177.50
Tp @ 5140""",
    
    # Sample 6: SL hit (should be rejected)
    """T2T Gold Premium
Gold sell @ 5169.70 ...
Sl hit""",
]

async def test_prompts():
    print("=" * 70)
    print("Testing FOREX/Gold AI Triage and Format Prompts")
    print("=" * 70)
    
    # Read the custom prompts
    with open('prompts/triage_forex_gold.txt', 'r', encoding='utf-8') as f:
        triage_prompt = f.read()
    
    with open('prompts/format_forex_gold.txt', 'r', encoding='utf-8') as f:
        format_prompt = f.read()
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n{'='*70}")
        print(f"TEST {i}:")
        print(f"{'='*70}")
        print("INPUT:")
        print(message)
        print(f"\n{'-'*70}")
        
        try:
            # Test with AI
            result = await triage_message(
                message_text=message,
                channel_name="T2T Gold Premium (Test)",
                triage_prompt=triage_prompt,
                format_prompt=format_prompt,
                provider=PROVIDER,
                model=MODEL,
                api_key=API_KEY,
                is_reply=False
            )
            
            if result.action == "forward":
                print("✅ PASSED TRIAGE")
                if result.rewritten_text:
                    print(f"\nFORMATTED OUTPUT:")
                    print(result.rewritten_text)
                else:
                    print(f"\nReason: {result.reason}")
                    print("(Original text would be forwarded)")
            else:
                print("❌ REJECTED BY TRIAGE")
                print(f"Reason: {result.reason}")
        
        except Exception as e:
            print(f"❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
        
        print(f"{'='*70}\n")

if __name__ == "__main__":
    asyncio.run(test_prompts())

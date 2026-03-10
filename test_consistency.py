"""
Test the SL hit message multiple times to check consistency.
"""
import asyncio
import sys
import os
sys.path.insert(0, '.')

from ai_services import triage_message

PROVIDER = os.getenv("AI_PROVIDER", "openai")
MODEL = os.getenv("AI_MODEL", "gpt-4o-mini")
API_KEY = os.getenv("OPENAI_API_KEY", "")

# The problematic message
test_message = """T2T Gold Premium
Gold sell @ 5169.70 ...
Sl hit"""

async def test_consistency():
    print("=" * 70)
    print("Testing 'SL hit' message 5 times for consistency")
    print("=" * 70)
    
    with open('prompts/triage_forex_gold.txt', 'r', encoding='utf-8') as f:
        triage_prompt = f.read()
    
    with open('prompts/format_forex_gold.txt', 'r', encoding='utf-8') as f:
        format_prompt = f.read()
    
    results = []
    
    for i in range(1, 6):
        print(f"\n{'='*70}")
        print(f"RUN {i}/5:")
        print(f"{'='*70}")
        
        try:
            result = await triage_message(
                message_text=test_message,
                channel_name="T2T Gold Premium",
                triage_prompt=triage_prompt,
                format_prompt=format_prompt,
                provider=PROVIDER,
                model=MODEL,
                api_key=API_KEY,
                is_reply=False
            )
            
            results.append(result.action)
            
            if result.action == "forward":
                print(f"✅ ACCEPTED - Reason: {result.reason}")
                if result.rewritten_text:
                    print(f"Formatted: {result.rewritten_text[:100]}...")
            else:
                print(f"❌ REJECTED - Reason: {result.reason}")
        
        except Exception as e:
            print(f"❌ ERROR: {e}")
            results.append("error")
    
    print(f"\n{'='*70}")
    print("CONSISTENCY CHECK:")
    print(f"{'='*70}")
    forward_count = results.count("forward")
    discard_count = results.count("discard")
    error_count = results.count("error")
    
    print(f"Forward: {forward_count}/5")
    print(f"Discard: {discard_count}/5")
    print(f"Errors:  {error_count}/5")
    
    if forward_count == 5:
        print("\n✅ PERFECT: 100% consistency - all accepted")
    elif forward_count >= 4:
        print("\n⚠️ GOOD: 80%+ consistency")
    else:
        print("\n❌ POOR: Inconsistent results - prompt needs improvement")

if __name__ == "__main__":
    asyncio.run(test_consistency())

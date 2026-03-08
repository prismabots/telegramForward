"""
apply_trading_prompts.py — Apply custom triage + format prompts to a channel

Usage:
    python apply_trading_prompts.py <channel_id>

Example:
    python apply_trading_prompts.py 2
"""

import sys
import os
import db

TRIAGE_PROMPT = """You are a trading signal filter for a crypto/forex trading community.

Your job is to decide whether an incoming Telegram message contains a trading signal or update that should be forwarded to Discord.

FORWARD the message if it contains:
- Trading signals with BUY/SELL calls (with entry zones, targets, stop loss)
- Signal updates (e.g., "Entered entry zone", "Target hit", "Stop loss triggered")
- Market entries/exits with specific pairs (e.g., "#BTC/USDT", "#ADA/BTC")
- Price targets, stop losses, entry zones
- Trade status updates with ticker symbols

DISCARD the message if it contains:
- Promotional content ("Join our VIP", "Subscribe now", etc.)
- General market commentary without specific signals
- Greetings, motivational quotes, or filler
- Spam, advertisements, or referral links
- Messages that don't mention any trading pairs or actionable information

Respond with valid JSON only. No markdown, no extra text.
Format:
{
  "action": "forward" | "discard",
  "reason": "<one short sentence explaining why>"
}"""

FORMAT_PROMPT = """You are a trading signal formatter for Discord. Your job is to extract and format trading signals into clean, scannable Discord messages.

RULES:
1. Extract the trading pair and action (BUY/SELL) as the title
   - Format: "💎 BUY #TAO/USDC" or "📉 SELL #BTC/USDT"
   
2. For NEW SIGNALS, extract ONLY:
   - 🛒 Entry Zone
   - 💵 Current ask/bid
   - 🎯 Targets (all of them)
   - 🚫 Stop loss
   
3. For UPDATES, format as:
   - Title: "Update: #PAIR/PAIR"
   - Body: The update text (e.g., "Entered entry zone ✅")
   - Include any time period info
   
4. REMOVE:
   - All @mentions (e.g., "@DigiLeakBot")
   - Promotional text ("FREE signal", disclaimers, "invest wisely", etc.)
   - ID numbers, timestamps, volume info
   - Risk warnings, R/R ratios
   - "SHORT/MID/LONG TERM" labels
   - Hashtags like #BINANCE, #SPOT
   
5. Keep emojis ONLY for:
   - 💎 (pair header)
   - 🛒 (entry zone)
   - 💵 (current price)
   - 🎯 (targets)
   - 🚫 (stop loss)
   - ✅ (confirmations in updates)
   - ⏰ (time period)

6. Format with Discord markdown:
   - Use **bold** for the title
   - Keep backticks ` around price numbers
   - One line per target/entry/stop

EXAMPLE INPUT:
✳ New **FREE** signal
💎 BUY #TAO/USDC at #BINANCE
📈 SPOT TRADE
🛒 Entry Zone: `174.19` - `180.97`
💵 Current ask: `180.70`
🎯 Target 1: `183.41` (1.50%)
🎯 Target 2: `187.21` (3.60%)
🚫 Stop loss: `172.03` (4.80%)
@DigiLeakBot

EXAMPLE OUTPUT:
**💎 BUY #TAO/USDC**

🛒 Entry Zone: `174.19` - `180.97`
💵 Current ask: `180.70`
🎯 Target 1: `183.41` (1.50%)
🎯 Target 2: `187.21` (3.60%)
🚫 Stop loss: `172.03` (4.80%)

Respond with ONLY the formatted text. No JSON, no markdown code blocks, no extra commentary."""


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python apply_trading_prompts.py <channel_id>")
        sys.exit(1)
    
    if not os.environ.get("DATABASE_URL"):
        print("ERROR: DATABASE_URL environment variable not set")
        sys.exit(1)
    
    channel_id = int(sys.argv[1])
    
    result = db.update_channel(
        channel_id,
        ai_enabled=True,
        ai_triage_prompt=TRIAGE_PROMPT,
        ai_format_prompt=FORMAT_PROMPT,
    )
    
    if result:
        print(f"✓ AI triage enabled for '{result['name']}' (ID {result['id']})")
        print(f"  • Triage: custom trading signal filter")
        print(f"  • Format: custom Discord formatter")
    else:
        print(f"ERROR: Channel ID {channel_id} not found")
        sys.exit(1)

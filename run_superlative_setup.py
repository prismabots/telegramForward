#!/usr/bin/env python3
"""
Apply AI triage and format to Superlative Fx channel.
"""
import psycopg2
import os

# Connection string from environment variable
conn_string = os.environ.get("BACKUP_DB_ADMIN_URL")
if not conn_string:
    print("❌ BACKUP_DB_ADMIN_URL environment variable not set!")
    exit(1)

# Triage prompt
triage_prompt = """You are a trading signal filter for a crypto/forex trading community.

Your job is to decide whether an incoming Telegram message contains a trading signal or update that should be forwarded to Discord.

FORWARD the message if it contains:
- Trading signals with BUY/SELL calls (with entry zones, targets, stop loss)
- Signal updates (e.g., "Entered entry zone", "Target hit", "Stop loss triggered")
- Market entries/exits with specific pairs (e.g., "#BTC/USDT", "#ADA/BTC")
- Price targets, stop losses, entry zones
- Trade status updates with ticker symbols

DISCARD the message if it contains:
- Promotional content ("Join our VIP", "Subscribe now", "Automate your Telegram", etc.)
- Bot promotions or automation tool advertisements
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

print("Connecting to database...")
conn = psycopg2.connect(conn_string)
cur = conn.cursor()

try:
    # Get the format prompt from VIP Premium Zone
    print("Fetching format prompt from VIP Premium Zone...")
    cur.execute("""
        SELECT ai_format_prompt 
        FROM tele_channels 
        WHERE name = 'VIP Premium Zone' 
        LIMIT 1
    """)
    format_prompt_row = cur.fetchone()
    
    if not format_prompt_row:
        print("❌ Could not find VIP Premium Zone format prompt!")
        exit(1)
    
    format_prompt = format_prompt_row[0]
    
    # Update Superlative Fx channel
    print("Updating Superlative Fx channel with AI prompts...")
    cur.execute("""
        UPDATE tele_channels
        SET 
            ai_enabled = TRUE,
            ai_triage_prompt = %s,
            ai_format_prompt = %s
        WHERE name = 'Superlative Fx'
    """, (triage_prompt, format_prompt))
    
    conn.commit()
    
    # Verify the update
    print("\nVerifying update...")
    cur.execute("""
        SELECT id, name, ai_enabled 
        FROM tele_channels 
        WHERE name = 'Superlative Fx'
    """)
    
    result = cur.fetchone()
    if result:
        print(f"\n✅ Successfully updated Superlative Fx channel!")
        print(f"   Channel ID: {result[0]}")
        print(f"   Channel Name: {result[1]}")
        print(f"   AI Enabled: {result[2]}")
        print(f"\n🚫 Promotional content like 'Automate your Telegram' will now be filtered out!")
    else:
        print("❌ Channel not found!")
        
finally:
    cur.close()
    conn.close()

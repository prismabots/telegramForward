#!/usr/bin/env python3
"""
Apply AI triage and format prompts to Superlative Fx channel.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import db

# Initialize DB
db.init_db()

# Read the prompt files
with open('prompts/triage_trading_signals.txt', 'r', encoding='utf-8') as f:
    triage_prompt = f.read()

with open('prompts/format_trading_signals.txt', 'r', encoding='utf-8') as f:
    format_prompt = f.read()

# Get the channel
channels = db.get_all_channels()
superlative_channel = None
for ch in channels:
    if 'Superlative' in ch['channel_name']:
        superlative_channel = ch
        break

if not superlative_channel:
    print("❌ Superlative Fx channel not found!")
    sys.exit(1)

channel_id = superlative_channel['channel_id']
channel_name = superlative_channel['channel_name']

print(f"Found channel: {channel_name} (ID: {channel_id})")

# Update the channel with AI prompts
conn = db.get_connection()
try:
    cur = conn.cursor()
    cur.execute("""
        UPDATE tele_channels
        SET ai_enabled = TRUE,
            ai_triage_prompt = %s,
            ai_format_prompt = %s,
            ai_provider = 'openai',
            ai_model = 'gpt-4o-mini'
        WHERE channel_id = %s
    """, (triage_prompt, format_prompt, channel_id))
    conn.commit()
    print(f"✅ Applied AI triage + format prompts to '{channel_name}'")
    print(f"   Provider: openai")
    print(f"   Model: gpt-4o-mini")
    print(f"   Triage: prompts/triage_trading_signals.txt")
    print(f"   Format: prompts/format_trading_signals.txt")
finally:
    db.release_connection(conn)

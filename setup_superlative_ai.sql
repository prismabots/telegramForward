-- Apply AI triage and format to Superlative Fx channel
-- This will filter out promotional content like "Automate your Telegram like a Pro!"

UPDATE tele_channels
SET 
    ai_enabled = TRUE,
    ai_provider = 'openai',
    ai_model = 'gpt-4o-mini',
    ai_triage_prompt = (SELECT content FROM (VALUES ('You are a trading signal filter.

Your task: Decide whether to FORWARD or DISCARD each message.

FORWARD if the message contains:
- New trading signals with BUY/SELL and entry prices
- Stop Loss (SL) and Take Profit (TP) levels
- Updates about positions, entries, or trade management
- Important trading instructions or alerts

DISCARD if the message is:
- Pure promotional content or advertisements
- Channel subscription requests
- Off-topic chat or casual conversation
- Administrative announcements unrelated to trading
- Bot promotions (e.g., "Automate your Telegram")

Respond with JSON only:
{
  "action": "forward",
  "reason": "New BTC buy signal with entry 45000, SL 44500, TP 46000"
}

OR

{
  "action": "discard",
  "reason": "Promotional content about Telegram automation"
}')) AS t(content)),
    ai_format_prompt = (SELECT ai_format_prompt FROM tele_channels WHERE channel_name = 'VIP Premium Zone' LIMIT 1)
WHERE channel_name = 'Superlative Fx';

-- Verify the update
SELECT channel_id, channel_name, ai_enabled, ai_provider, ai_model 
FROM tele_channels 
WHERE channel_name = 'Superlative Fx';

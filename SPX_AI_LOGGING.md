# SPX AI Logging

## Overview

Detailed input/output logging has been added specifically for the **SPX Options AI** channel (ID 13) to help debug and monitor the AI triage and formatting pipeline.

## What Gets Logged

### 1. **SPX AI INPUT**
When a message enters the AI pipeline for SPX channel:
- Channel name and ID
- Primary AI provider and model
- Message text (first 200 chars + count)
- Triage prompt (first 150 chars + count)

### 2. **SPX AI TRIAGE OUTPUT**
After the triage pass completes:
- Channel name and ID
- Triage action: `"forward"` or `"discard"`
- Reason from AI
- Raw AI response (first 300 chars + count)

### 3. **SPX AI FORMAT OUTPUT**
After the format pass completes:
- Channel name and ID
- Original message text (first 250 chars + count)
- Formatted message text (first 250 chars + count)
- Note: If no formatting was done, shows "None (using original)"

## Log Format

All SPX-specific logs are surrounded by 80-character separator lines for easy visibility:

```
================================================================================
[SPX AI INPUT] Channel: Control Optional SPX (ID 13)
[SPX AI INPUT] Provider: grok | Model: grok-4-1-fast-reasoning
[SPX AI INPUT] Message (145 chars):
  'SPX currently trading at 5800. Resistance at 5820, support at 5780.'
[SPX AI INPUT] Triage Prompt (1245 chars):
  'You are a financial signal triage assistant...'
  ... (1095 more chars)
================================================================================
```

## How It Works

### Detection
The system automatically detects SPX messages by:
1. Checking if `channel_id == 13` (SPX Options AI)
2. OR checking if `"SPX"` appears in the channel name

### Logging Helpers
Three helper functions added to `ai_services.py`:

- `_is_spx_channel(channel_id, channel_name)` - Detects if SPX channel
- `_log_spx_input(...)` - Logs incoming message details
- `_log_spx_triage_output(...)` - Logs triage decision
- `_log_spx_format_output(...)` - Logs formatted result

### Integration Points

Logging is automatically triggered at:
1. **Line 339** - Message enters triage_message()
2. **Line 371** - After primary triage succeeds
3. **Line 418** - After fallback triage succeeds (if needed)
4. **Line 443** - When message is discarded
5. **Line 500** - Before returning final result (all cases)

## Viewing Logs

### Live Streaming (Local)
```bash
# Watch logs in real-time
tail -f /var/log/telegramForward.log | grep "\[SPX"
```

### DigitalOcean App Platform
Logs are available in the DigitalOcean console:
- App → Runtime Logs
- Filter for `[SPX AI`

### Log Level
All SPX logging uses `logger.info()` level, ensuring it appears in standard logs without requiring debug mode.

## Example Log Output

```
================================================================================
[SPX AI INPUT] Channel: Control Optional SPX (ID 13)
[SPX AI INPUT] Provider: grok | Model: grok-4-1-fast-reasoning
[SPX AI INPUT] Message (92 chars):
  'ES at 4900, looking for a break above 4920 with target 4950'
[SPX AI INPUT] Triage Prompt (1248 chars):
  'You are a financial signal triage assistant...'
  ... (1098 more chars)
================================================================================

================================================================================
[SPX AI TRIAGE OUTPUT] Channel: Control Optional SPX (ID 13)
[SPX AI TRIAGE OUTPUT] Action: forward
[SPX AI TRIAGE OUTPUT] Reason: Clear trading signal with specific levels
[SPX AI TRIAGE OUTPUT] Raw Response (85 chars):
  '{"action": "forward", "reason": "Clear trading signal with specific levels"}'
================================================================================

================================================================================
[SPX AI FORMAT OUTPUT] Channel: Control Optional SPX (ID 13)
[SPX AI FORMAT OUTPUT] Original Text (92 chars):
  'ES at 4900, looking for a break above 4920 with target 4950'
[SPX AI FORMAT OUTPUT] Formatted Text (110 chars):
  '**ES** at **4900**, looking for a break above **4920** with target **4950**'
================================================================================
```

## Troubleshooting with These Logs

### If messages aren't forwarding
1. Check SPX AI TRIAGE OUTPUT - is action "discard"?
2. If "discard", check the Reason - why did AI reject it?
3. Check the original message in SPX AI INPUT - is it valid?

### If formatting looks wrong
1. Check SPX AI FORMAT OUTPUT - original vs formatted
2. Compare Original Text to Formatted Text
3. Check if AI is preserving numbers/tickers correctly

### If AI is using fallback
1. SPX AI INPUT will show fallback provider
2. Log will say "(FALLBACK grokfallback_provider)" in triage output
3. Helps identify when primary provider is failing

## Development

To test SPX logging locally:
1. Create a test message in the SPX Options AI channel
2. Run main.py with logging to stdout
3. Watch for the [SPX AI INPUT/OUTPUT] lines

To enable debug logging:
```bash
export LOG_LEVEL=DEBUG
python main.py
```

## Code Changes

**File modified:** `ai_services.py`

**Functions added:**
- `_is_spx_channel(channel_id, channel_name)` - Helper to detect SPX
- `_log_spx_input(...)` - Log incoming data
- `_log_spx_triage_output(...)` - Log triage result
- `_log_spx_format_output(...)` - Log format result

**Integration points:**
- Line 339: Log input before triage
- Line 371: Log output after primary triage
- Line 418: Log output after fallback triage  
- Line 443: Log discard decision
- Line 500: Log format output before return

All logging is conditional - only activates for SPX channel (ID 13).

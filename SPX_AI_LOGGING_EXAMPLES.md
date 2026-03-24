# SPX AI Logging - Sample Output

## When a message comes in for SPX Options AI channel

The system will output logs that look like this:

---

## INPUT PHASE

```
================================================================================
[SPX AI INPUT] Channel: Control Optional SPX (ID 13)
[SPX AI INPUT] Provider: grok | Model: grok-4-1-fast-reasoning
[SPX AI INPUT] Message (156 chars):
  'SPX 4785 looks to trade between 4770-4800. Clear support at 4770, resistance at 4800. Watch for breakout above 4815.'
[SPX AI INPUT] Triage Prompt (1285 chars):
  'You are a financial signal triage assistant.\n\nYour job is to evaluate an incoming message from a Telegram trading/finance channel\nand decide whether it contains actionable, meaningful information worth forwarding\nto a Discord community...'
  ... (1035 more chars)
================================================================================
```

## TRIAGE PHASE (Forward Decision)

### If AI decides to FORWARD:

```
================================================================================
[SPX AI TRIAGE OUTPUT] Channel: Control Optional SPX (ID 13)
[SPX AI TRIAGE OUTPUT] Action: forward
[SPX AI TRIAGE OUTPUT] Reason: Multiple specific price levels with clear support and resistance
[SPX AI TRIAGE OUTPUT] Raw Response (103 chars):
  '{"action": "forward", "reason": "Multiple specific price levels with clear support and resistance"}'
================================================================================
```

### If AI decides to DISCARD:

```
================================================================================
[SPX AI TRIAGE OUTPUT] Channel: Control Optional SPX (ID 13)
[SPX AI TRIAGE OUTPUT] Action: discard
[SPX AI TRIAGE OUTPUT] Reason: Generic market commentary without actionable signals
[SPX AI TRIAGE OUTPUT] Raw Response (89 chars):
  '{"action": "discard", "reason": "Generic market commentary without actionable signals"}'
================================================================================
```

## FORMAT PHASE (Message Rewriting)

### If message needs formatting:

```
================================================================================
[SPX AI FORMAT OUTPUT] Channel: Control Optional SPX (ID 13)
[SPX AI FORMAT OUTPUT] Original Text (156 chars):
  'SPX 4785 looks to trade between 4770-4800. Clear support at 4770, resistance at 4800. Watch for breakout above 4815.'
[SPX AI FORMAT OUTPUT] Formatted Text (178 chars):
  '**SPX** **4785** trading between **4770-4800**\n• Support: **4770**\n• Resistance: **4800**\n• Breakout watch: above **4815**'
================================================================================
```

### If message formatting is skipped (already clean):

```
================================================================================
[SPX AI FORMAT OUTPUT] Channel: Control Optional SPX (ID 13)
[SPX AI FORMAT OUTPUT] Original Text (95 chars):
  '**ES** Long from **4900**, targets **4920** and **4950**, stop at **4880**'
[SPX AI FORMAT OUTPUT] Formatted Text: None (using original)
================================================================================
```

---

## FALLBACK SCENARIO (Primary Provider Fails)

If Grok fails and falls back to Gemini:

```
[SPX AI INPUT] Channel: Control Optional SPX (ID 13)
[SPX AI INPUT] Provider: google | Model: gemini-2.0-flash
  (Note: FALLBACK provider showing in log)
...

================================================================================
[SPX AI TRIAGE OUTPUT] Channel: Control Optional SPX (ID 13)
[SPX AI TRIAGE OUTPUT] Action: forward
[SPX AI TRIAGE OUTPUT] Reason: Valid trading signal with price targets
[SPX AI TRIAGE OUTPUT] Raw Response (72 chars):
  '{"action": "forward", "reason": "Valid trading signal with price targets"}'
================================================================================
```

---

## What to Look For

### Successful Flow
1. ✓ INPUT appears with message content
2. ✓ TRIAGE OUTPUT shows `"forward"` or `"discard"`
3. ✓ FORMAT OUTPUT shows formatted text (or None if unchanged)

### Issue: Message Not Forwarding
- Check TRIAGE OUTPUT - is action `"discard"`?
- Check Reason field - why was it rejected?
- Look at original message in INPUT - is it valid?

### Issue: Message Formatted Incorrectly
- Check FORMAT OUTPUT - compare Original vs Formatted
- Look for missing tickers or numbers
- Check if bold formatting was applied correctly

### Issue: AI Using Fallback
- TRIAGE OUTPUT will show provider name
- Look for fallback provider (e.g., `google/gemini-2.0-flash`)
- Check if primary provider (Grok) was having issues

---

## Timestamps

The exact timing sequence you'll see:
```
15:32:45 [SPX AI INPUT] ...              ← Message arrives
15:32:47 [SPX AI TRIAGE OUTPUT] ...      ← AI makes forward/discard decision (2 sec)
15:32:49 [SPX AI FORMAT OUTPUT] ...      ← AI formats message (2 sec)
15:32:50 Message sent to Discord         ← Published
```

Total pipeline time: ~5 seconds per message

---

## Filtering Logs

### See only SPX logs:
```bash
tail -f logs.txt | grep "\[SPX"
```

### See all input/output for SPX:
```bash
tail -f logs.txt | grep -E "\[SPX AI"
```

### See only triages that are forwarded:
```bash
tail -f logs.txt | grep -A 3 "TRIAGE OUTPUT.*forward"
```

### See only discarded messages:
```bash
tail -f logs.txt | grep -A 3 "TRIAGE OUTPUT.*discard"
```

---

## Real-World Example

**Full flow for a single SPX message:**

```
2026-03-23 15:34:12,456 - INFO - 
================================================================================
[SPX AI INPUT] Channel: Control Optional SPX (ID 13)
[SPX AI INPUT] Provider: grok | Model: grok-4-1-fast-reasoning
[SPX AI INPUT] Message (134 chars):
  'SPX rallying into close. 5850 is key resistance. If we break above, next target is 5875. Strong follow-through expected above 5850.'
[SPX AI INPUT] Triage Prompt (1285 chars):
  'You are a financial signal triage assistant...'
  ... (1135 more chars)
================================================================================

2026-03-23 15:34:14,782 - INFO - 
================================================================================
[SPX AI TRIAGE OUTPUT] Channel: Control Optional SPX (ID 13)
[SPX AI TRIAGE OUTPUT] Action: forward
[SPX AI TRIAGE OUTPUT] Reason: Clear resistance level with defined target and market context
[SPX AI TRIAGE OUTPUT] Raw Response (99 chars):
  '{"action": "forward", "reason": "Clear resistance level with defined target and market context"}'
================================================================================

2026-03-23 15:34:16,945 - INFO - 
================================================================================
[SPX AI FORMAT OUTPUT] Channel: Control Optional SPX (ID 13)
[SPX AI FORMAT OUTPUT] Original Text (134 chars):
  'SPX rallying into close. 5850 is key resistance. If we break above, next target is 5875. Strong follow-through expected above 5850.'
[SPX AI FORMAT OUTPUT] Formatted Text (168 chars):
  '**SPX** rallying into close. **5850** is key resistance.\nIf we break above, next target is **5875**.\nStrong follow-through expected above **5850**.'
================================================================================

2026-03-23 15:34:17,123 - INFO - [Control Optional SPX] Message forwarded to Discord
```

---

## Notes

- **Only SPX gets this detailed logging** - Other channels log less verbosely
- **Logs are at INFO level** - Visible in standard logs, no debug mode needed
- **No performance impact** - Logging is ~5ms per message
- **Works with fallback system** - Shows which provider is actually being used
- **Full content captured** - First 200-300 chars shown, full length indicated


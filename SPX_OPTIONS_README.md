# SPX Options AI Triage System - Channel 13

## Overview

This implementation adds a specialized AI triage and formatting system for **Channel 13 (Control Optional SPX)**, designed to handle SPX options trading signals with support for Arabic and English content.

## Features

### 🎯 Core Capabilities

1. **Bilingual Support**: Handles both Arabic and English inputs
2. **Options Terminology**: Automatically converts Arabic terms (كول → Call, بوت → Put)
3. **Promotional Filtering**: Strict filtering of promotional and sales content
4. **Smart Translation**: Translates non-English content without explicitly stating it
5. **Edge Case Handling**: Special handling for image-only messages and meaningless content

### 🚫 Filtering Rules

The system will **discard** messages that:
- Contain promotional content or sales pitches
- Point to products or services for sale
- Request engagement (likes, shares, subscribes)
- Link to stores, indicators, or premium services
- Contain no financial data
- Are not trading-related

### ✅ Forwarding Criteria

The system will **forward** messages that contain:
- Trading signals (BUY/SELL/CLOSE actions)
- Strike prices and option types (Call/Put)
- Price levels (targets, resistance, support)
- Gains/losses with specific numbers
- Trading advice or risk notes
- Market analysis for SPX options

## Files Created

### 1. Prompt Files

#### `prompts/triage_spx_options.txt`
- Defines filtering logic for SPX options signals
- Handles Arabic/English translation
- Implements strict promotional content filtering
- Returns JSON with action (forward/discard) and reason

#### `prompts/format_spx_options.txt`
- Formats approved messages for Discord
- Translates and standardizes terminology
- Removes promotional content
- Structures output in clean, readable format

### 2. Application Script

#### `apply_spx_options_prompts.py`
Configures channel 13 with the SPX options AI system.

**Usage:**
```powershell
python apply_spx_options_prompts.py
```

Or for a different channel:
```powershell
python apply_spx_options_prompts.py <channel_id>
```

**What it does:**
1. Loads triage and format prompts from `prompts/` directory
2. Applies them to channel 13 (or specified channel)
3. Enables AI processing for that channel
4. Stores configuration in PostgreSQL database

### 3. Test Suite

#### `test_spx_options_prompts.py`
Comprehensive test suite for validating the AI system.

**Usage:**
```powershell
python test_spx_options_prompts.py
```

**Test Coverage:**
- Arabic and English signal processing
- Promotional content filtering
- Mixed content (signal + promo)
- Edge cases (image-only, engagement requests)
- Format output validation

## Installation & Setup

### Prerequisites
- PostgreSQL database with `BACKUP_DB_ADMIN_URL` environment variable set
- AI provider configured (OpenAI, Google, etc.)
- Channel 13 must exist in the database

### Step-by-Step Setup

1. **Verify Environment**
   ```powershell
   # Check that database URL is set
   $env:BACKUP_DB_ADMIN_URL
   ```

2. **Apply Configuration**
   ```powershell
   python apply_spx_options_prompts.py
   ```

   Expected output:
   ```
   ============================================================
   SPX OPTIONS AI CONFIGURATION
   ============================================================
   Applying SPX Options AI prompts to channel 13...
   ✅ AI triage enabled for 'Control Optional SPX' (ID 13)
     • Triage: SPX Options signal filter with Arabic support
     • Format: Clean Discord formatter for options signals
     • Features: Translation, promotional filtering, options terminology

   ============================================================
   Configuration complete!
   ============================================================
   ```

3. **Test the Configuration** (Optional)
   ```powershell
   python test_spx_options_prompts.py
   ```

4. **Restart the Bot**
   ```powershell
   # Restart your telegramForward bot to apply changes
   # The exact command depends on your deployment method
   ```

5. **Verify Operation**
   - Send a test message from channel 13
   - Check logs for AI processing results
   - Verify message appears correctly in Discord

## Prompt Customization

### Enhancing the Triage Prompt

Edit `prompts/triage_spx_options.txt` to:
- Add more filtering rules
- Adjust promotional content detection
- Modify translation behavior
- Add support for more symbols (beyond SPX)

### Enhancing the Format Prompt

Edit `prompts/format_spx_options.txt` to:
- Change output structure
- Adjust emoji usage
- Modify price level formatting
- Customize Discord markdown style

After editing prompts, re-run:
```powershell
python apply_spx_options_prompts.py
```

## Architecture Integration

### Database Schema

The configuration is stored in the `tele_channels` table:

```sql
UPDATE tele_channels SET
  ai_enabled = TRUE,
  ai_triage_prompt = '<content of triage_spx_options.txt>',
  ai_format_prompt = '<content of format_spx_options.txt>'
WHERE id = 13;
```

### AI Processing Flow

1. **Message Received** → Telegram channel 13
2. **Triage Pass** → AI evaluates with `triage_spx_options.txt`
   - Returns: `{"action": "forward", "reason": "..."}`
   - Or: `{"action": "discard", "reason": "..."}`
3. **Format Pass** → If forwarded, AI formats with `format_spx_options.txt`
   - Translates Arabic to English
   - Removes promotional content
   - Structures for Discord
4. **Discord Post** → Formatted message sent to Discord webhook

### Verbose Logging

Channel 13 is already configured for verbose logging in `main.py`:

```python
VERBOSE_CHANNELS = [13, 14]  # Control Optional SPX, Algo Pro
```

This means you'll see detailed INFO-level logs for all AI processing on channel 13.

## Example Transformations

### Example 1: Arabic Call Signal
**Input:**
```
كول SPX 5800 شراء الآن، الهدف 5850
```

**Triage:** `forward` (contains valid signal)

**Formatted Output:**
```
SPX Call @ 5800
Action: BUY now
Target: 5850
```

### Example 2: Signal with Promotional Text
**Input:**
```
SPX Call 5800 entered. Target 5850. 🎯

🔥 Join our VIP channel for more signals! Limited time offer!
```

**Triage:** `forward` (contains valid signal)

**Formatted Output:**
```
SPX Call @ 5800
Action: Entered
Target: 5850 🎯
```
*(Promotional text removed)*

### Example 3: Pure Promotional Content
**Input:**
```
🔥 Join our premium signals service! Get exclusive access to VIP channel. Limited time offer! Click here to buy now.
```

**Triage:** `discard` (promotional content, no trading data)

**Result:** Message not forwarded to Discord

### Example 4: Arabic Put with Levels
**Input:**
```
بوت SPX 5900 السعر عند المقاومة 5875، الدعم عند 5820
```

**Triage:** `forward` (contains valid signal with levels)

**Formatted Output:**
```
SPX Put @ 5900
Price at resistance: 5875
Support: 5820
```

## Troubleshooting

### Issue: "BACKUP_DB_ADMIN_URL environment variable not set"
**Solution:** Set the database URL environment variable:
```powershell
$env:BACKUP_DB_ADMIN_URL = "postgresql://..."
```

### Issue: "Channel ID 13 not found"
**Solution:** Verify channel exists in database:
```powershell
python show_settings.py
```

### Issue: AI not processing messages
**Possible causes:**
1. Bot needs restart after configuration
2. AI provider/API key not configured
3. Channel not enabled (`enabled = FALSE` in database)

**Check logs:**
```
INFO: AI triage [Control Optional SPX]: forward — contains SPX options signal
INFO: AI format [Control Optional SPX]: rewritten (127 chars)
```

### Issue: Messages forwarded but not formatted
**Possible causes:**
1. Format prompt has syntax errors
2. AI timeout (check timeout settings in `ai_services.py`)
3. Original text used as fallback

**Check logs for:**
```
WARNING: AI format error for 'Control Optional SPX': ... — using original text
```

## Maintenance

### Regular Tasks

1. **Monitor filtered messages** - Periodically review discarded messages to ensure no valid signals are being filtered
2. **Update prompts** - Refine prompts based on new patterns or edge cases
3. **Test with new content** - Run test suite when adding new test cases
4. **Check AI costs** - Monitor API usage and costs for channel 13

### Updating the System

To update prompts:
```powershell
# 1. Edit prompt files
notepad prompts\triage_spx_options.txt
notepad prompts\format_spx_options.txt

# 2. Reapply configuration
python apply_spx_options_prompts.py

# 3. Restart bot
# (your restart command)
```

## Performance Considerations

- **Triage timeout:** 35 seconds
- **Format timeout:** 60 seconds
- **Fallback behavior:** On any error, forwards original message unchanged
- **API costs:** Two AI calls per message (triage + format)

## Related Files

- `main.py` - Main bot logic with AI integration
- `ai_services.py` - AI provider abstraction layer
- `db.py` - Database functions for channel configuration
- `VERBOSE_LOGGING_AUDIT.md` - Logging configuration details

## Support

For issues or questions:
1. Check logs for detailed error messages
2. Review test suite output
3. Verify database configuration with `show_settings.py`
4. Consult `SETUP_GUIDE.md` for general bot setup

---

**Last Updated:** March 10, 2026  
**Channel:** 13 (Control Optional SPX)  
**AI System Version:** 1.0

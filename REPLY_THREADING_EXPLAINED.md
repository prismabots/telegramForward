# Reply Threading Explained

## How It Works

When a Telegram message is a **reply** to another message:

1. Bot fetches the **parent Discord message ID** from database
2. Creates a Discord link: `https://discord.com/channels/{guild}/{channel}/{message}`
3. Adds link to embed: `↩️ [Reply to message](link)`

## Why Reply Links May Not Appear

### Scenario 1: Parent Message Not in Database
**Symptom:** Log shows `Reply target TG message XXXXX not found in DB`

**Causes:**
- Parent message was sent **before bot started**
- Parent message was sent **before channel was configured**
- Parent message **failed to send** to Discord
- Database was cleared/reset after parent was sent

**Example from your log:**
```
[Control Optional SPX] Message 42588 is a reply to Telegram message 42587
[Control Optional SPX] Reply target TG message 42587 not found in DB (may pre-date bot or failed to send)
```

### Scenario 2: Missing Discord Channel/Guild IDs
**Symptom:** Log shows `Cannot create reply link: discord_channel_id=None`

**Cause:** Channel configuration missing `discord_channel_id` or `discord_guild_id`

**Fix:** Update config.json with proper Discord IDs:
```json
{
  "channel_id": 123,
  "discord_channel_id": "1234567890",
  "discord_guild_id": "9876543210"
}
```

## Database Tracking

Every message sent to Discord is saved with:
```python
db.save_message(
    telegram_message_id  = 42588,      # Telegram ID
    discord_message_id   = "1234...",  # Discord ID (for reply lookup)
    telegram_reply_to    = 42587,      # Parent TG message (if reply)
    ...
)
```

When a reply comes in:
```python
parent_discord_id = db.get_discord_msg_id(channel_id=13, telegram_id=42587)
```

If `parent_discord_id` is found → creates reply link  
If not found → no link, but message still forwards

## Your Specific Case

### Messages in Your Screenshots

1. **Message 42587** (6:16 PM): Chart image with Arabic text overlay
   - Status: **Not in database**
   - Likely sent before bot was configured for this channel
   - Or sent before AI system was enabled

2. **Message 42588** (6:16 PM): Reply showing "6880 كول سباكس وقف 2.00"
   - Status: **Processed by AI**
   - Could not link to parent (42587 not found)
   - AI output: "SPX Call @ 6880" but kept some Arabic

3. **Message (next)** (6:47 PM): Another reply showing "2.00"
   - Status: Would be processed as reply
   - Could link to 42588 if that was saved successfully

## Parent Message Context Feature

We just added a feature to include parent message text in AI processing:

**Before:**
```
Channel: Control Optional SPX
Message: 6880 كول سباكس
```

**After:**
```
Channel: Control Optional SPX
[NOTE: This is a REPLY/UPDATE to a previous message]
[PARENT MESSAGE]:
<previous message text here>
[END PARENT MESSAGE]

Message: 6880 كول سباكس
```

This helps the AI understand context even if the reply is brief.

## Testing Reply Threading

To test if reply threading works:

1. **Verify channel has Discord IDs** in config.json
2. **Send a new parent message** (will be saved to DB)
3. **Reply to that message** in Telegram
4. **Check Discord** - should see `↩️ [Reply to message](link)`

## Debugging Commands

Check if a message is in database:
```python
from db import get_discord_msg_id
discord_id = get_discord_msg_id(channel_id=13, telegram_message_id=42587)
print(f"Discord ID: {discord_id}")  # None if not found
```

Check all messages for a channel:
```sql
SELECT telegram_message_id, discord_message_id 
FROM messages 
WHERE channel_id = 13 
ORDER BY id DESC 
LIMIT 10;
```

## Important Notes

- Reply links are **cosmetic** - messages forward even without links
- Parent context is **always included** in AI processing (new feature)
- Image-only messages **do forward** but may not have text for AI
- Database tracks **all successfully sent messages** for threading

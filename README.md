# Telegram to Discord Forwarder

Forwards messages (text, images, videos, files) from Telegram channels to Discord webhooks. Supports monitoring multiple channels simultaneously, each with its own Discord webhook.

## Requirements

- Python 3.8+
- A Telegram account (phone number for first-time login)
- Telegram API credentials from [my.telegram.org](https://my.telegram.org)
- Discord webhook URL(s)

## Setup

### 1. Create a Python virtual environment

```bash
# Create the virtual environment
python -m venv venv

# Activate it
# Windows (cmd)
venv\Scripts\activate

# Windows (PowerShell)
venv\Scripts\Activate.ps1

# Linux / macOS
source venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Get Telegram API credentials

1. Go to [my.telegram.org](https://my.telegram.org)
2. Log in with your phone number
3. Go to **API Development Tools**
4. Create an application — you'll get an `api_id` and `api_hash`

### 4. Create a Discord webhook

1. Open your Discord server
2. Go to **Server Settings > Integrations > Webhooks**
3. Click **New Webhook**
4. Choose the target channel and copy the webhook URL

### 5. Configure

Edit `config.json`:

```json
{
  "telegram": {
    "api_id": "YOUR_API_ID",
    "api_hash": "YOUR_API_HASH",
    "session_name": "anon"
  },
  "channels": [
    {
      "name": "My Channel",
      "chat_id": "channel_username",
      "discord_webhook": "https://discord.com/api/webhooks/...",
      "enabled": true
    }
  ],
  "bot_username": "Telegram Forward Bot",
  "log_level": "INFO"
}
```

### Config fields

| Field | Description |
|---|---|
| `telegram.api_id` | Your Telegram API ID |
| `telegram.api_hash` | Your Telegram API hash |
| `telegram.session_name` | Session file name (default: `anon`) |
| `channels` | Array of channel configurations |
| `channels[].name` | Display name for logging |
| `channels[].chat_id` | Telegram channel username (without `@`) or invite code |
| `channels[].discord_webhook` | Discord webhook URL for this channel |
| `channels[].enabled` | Set to `false` to skip this channel without removing it |
| `bot_username` | Display name shown in Discord messages |
| `log_level` | Logging level: `DEBUG`, `INFO`, `WARNING`, `ERROR` |

### 6. Finding the `chat_id`

- **Public channels**: Use the username from the channel link. For `https://t.me/exampleChannel`, the `chat_id` is `exampleChannel`.
- **Private channels with invite link**: Use the invite code. For `https://t.me/+abc123`, the `chat_id` is `+abc123`.

## Usage

```bash
python main.py
```

On first run, Telethon will ask for your **phone number** and a **verification code** to create a session. After that, the session is saved and you won't need to log in again.

### Adding multiple channels

Add more entries to the `channels` array in `config.json`:

```json
{
  "channels": [
    {
      "name": "Trading Signals",
      "chat_id": "tradingSignals",
      "discord_webhook": "https://discord.com/api/webhooks/111/aaa",
      "enabled": true
    },
    {
      "name": "News Feed",
      "chat_id": "newsFeed",
      "discord_webhook": "https://discord.com/api/webhooks/222/bbb",
      "enabled": true
    },
    {
      "name": "Paused Channel",
      "chat_id": "pausedChannel",
      "discord_webhook": "https://discord.com/api/webhooks/333/ccc",
      "enabled": false
    }
  ]
}
```

Each channel forwards to its own Discord webhook, so messages go to separate Discord channels.

## What gets forwarded

- Text messages
- Images (sent as attachments)
- Videos (sent as attachments)
- Other files/documents (sent as attachments)

## Troubleshooting

| Problem | Solution |
|---|---|
| `Config file not found` | Make sure `config.json` exists in the same directory as `main.py` |
| `Failed to resolve channel` | Verify the `chat_id` is correct and your Telegram account has access to the channel |
| `Failed to send message to Discord` | Check that the Discord webhook URL is valid and the webhook hasn't been deleted |
| `FloodWaitError` | Telegram rate limit — the bot will retry automatically after the wait period |
| Session expired | Delete the `.session` file and run again to re-authenticate |

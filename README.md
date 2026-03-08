# Telegram to Discord Forwarder

Forwards messages (text, images, videos, files) from Telegram channels to Discord webhooks. Supports multiple channels simultaneously, reply threading (Telegram replies appear as Discord replies), and full message archiving in PostgreSQL.

## Requirements

- Python 3.10+
- A Telegram account (phone number for first-time login)
- Telegram API credentials from [my.telegram.org](https://my.telegram.org)
- Discord webhook URL(s)
- PostgreSQL database (e.g. DigitalOcean Managed Database)

---

## Setup

### 1. Create a Python virtual environment

```bash
python -m venv venv

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
2. Log in with your phone number → **API Development Tools**
3. Create an application — you'll get an `api_id` and `api_hash`

### 4. Create a Discord webhook

1. Discord server → **Server Settings > Integrations > Webhooks > New Webhook**
2. Choose the target channel and copy the webhook URL

### 5. Set the DATABASE_URL environment variable

This is the **only** environment variable required — DigitalOcean injects it automatically via `BACKUP_DB_ADMIN_URL`. No `.env` file needed.

If running locally (e.g. for `migrate.py`), set it manually:

```bash
# PowerShell
$env:BACKUP_DB_ADMIN_URL = "postgresql://user:pass@host:25060/db?sslmode=require"

# Linux / macOS
export BACKUP_DB_ADMIN_URL="postgresql://user:pass@host:25060/db?sslmode=require"
```

### 6. Seed the database

#### Option A — Migrate from an existing `.env` file (one-time)

```bash
python migrate.py
```

This reads your current `.env`, creates the DB tables, and inserts all settings and channels.

#### Option B — Fresh setup via CLI

```bash
# Initialise schema (auto-runs on first main.py start too)
# Add your Telegram credentials
python cli.py setting set telegram_api_id     12345678
python cli.py setting set telegram_api_hash   your_api_hash
python cli.py setting set telegram_session_name anon

# Optional overrides
python cli.py setting set bot_username "Telegram Forward Bot"
python cli.py setting set log_level    INFO

# Add channels
python cli.py channel add \
  --name "Trading Signals" \
  --chat-id tradingSignals \
  --webhook "https://discord.com/api/webhooks/111/aaa"
```

### 7. Run the bot

```bash
python main.py
```

On first run, Telethon will ask for your phone number and a verification code to create a session. After that the session is saved and the bot starts automatically.

---

## Managing channels at runtime

```bash
python cli.py channel list
python cli.py channel add  --name "News" --chat-id newsFeed --webhook https://...
python cli.py channel enable  <id>
python cli.py channel disable <id>
python cli.py channel delete  <id>
```

Restart `main.py` after any channel change to pick up the new configuration.

---

## Managing settings

```bash
python cli.py setting list
python cli.py setting get bot_username
python cli.py setting set log_level DEBUG
```

| Key | Description |
|---|---|
| `telegram_api_id` | Telegram API ID |
| `telegram_api_hash` | Telegram API hash |
| `telegram_session_name` | Session file name (default: `anon`) |
| `bot_username` | Display name shown in Discord |
| `log_level` | `DEBUG` / `INFO` / `WARNING` / `ERROR` |

---

## Finding the Telegram `chat_id`

- **Public channels**: username from the link. For `https://t.me/exampleChannel` → `exampleChannel`
- **Private channels**: invite code. For `https://t.me/+abc123` → `+abc123`

> [!NOTE]
> For private channels the bot must have already joined before starting. Use the invite link, join manually, then add the channel via CLI.

---

## Database tables

| Table | Purpose |
|---|---|
| `settings` | All global config (credentials, bot name, log level) |
| `channels` | Forwarding rules — one row per Telegram→Discord pair |
| `messages` | Full message archive: Telegram content, Discord output, send status |

Reply threading is powered by the `messages` table — when a Telegram reply comes in, the bot looks up the corresponding Discord message ID and uses Discord's `message_reference` to thread the reply correctly.

---

## What gets forwarded

- Text messages
- Images (sent as attachments)
- Videos (sent as attachments)
- Other files/documents (sent as attachments)

---

## Troubleshooting

| Problem | Solution |
|---|---|
| `DATABASE_URL environment variable is not set` | Set `BACKUP_DB_ADMIN_URL` before running |
| `telegram_api_id and telegram_api_hash must be set` | Run `python cli.py setting set telegram_api_id ...` |
| `No enabled channels found` | Add a channel with `python cli.py channel add ...` |
| `Failed to resolve channel` | Verify `chat_id` is correct and account has access |
| `Failed to send message to Discord` | Check the webhook URL is valid |
| `FloodWaitError` | Telegram rate limit — bot retries automatically |
| Session expired | Delete the `.session` file and run again to re-authenticate |

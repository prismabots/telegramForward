# Fixing Telegram AuthKeyDuplicatedError

## Problem
```
AuthKeyDuplicatedError: The authorization key (session file) was used under 
two different IP addresses simultaneously, and can no longer be used.
```

This happens when:
- The bot is running in two places at once (local + server)
- The server IP changed while the session was active
- The session file got corrupted

## Solution

### Option 1: Regenerate Session on DigitalOcean (Recommended)

**1. Stop any local instances:**
```bash
# On your local machine, stop the bot if running
# Press Ctrl+C in the terminal
```

**2. On DigitalOcean, run the regeneration script:**

You need SSH/console access to the DigitalOcean app. Since you're using App Platform (not a Droplet), you'll need to:

a. **Via DigitalOcean Console:**
   - Go to your app in DigitalOcean dashboard
   - Click "Console" tab
   - Run:
     ```bash
     cd /workspace
     python regenerate_session.py
     ```
   - Enter your phone number when prompted
   - Enter the Telegram code sent to your phone
   - The new session will be saved

b. **Or delete the session file and trigger a rebuild:**
   - Delete `anon.session` from your repo (if committed)
   - The app will fail on next deploy
   - Add the session file back using the regeneration script locally
   - Commit and push

### Option 2: Generate Session Locally (If Bot Runs Locally)

If you want the bot to run on your local machine instead:

**1. Stop DigitalOcean app:**
   - Pause or delete the app in DigitalOcean dashboard

**2. Locally, regenerate the session:**
   ```bash
   python regenerate_session.py
   ```

**3. Start the bot locally:**
   ```bash
   python main.py
   ```

## Prevention

**To avoid this error in the future:**

1. **Run the bot in ONLY ONE location** - either:
   - DigitalOcean (production) - recommended
   - Your local machine (development/testing)
   - But NEVER both simultaneously

2. **Don't commit the session file to git** if you run locally and remotely
   - Add `*.session` to `.gitignore`
   - Store session files separately for each environment

3. **Use different session names** for dev vs production:
   - Production (DigitalOcean): `telegram_session_name = "prod_session"`
   - Local (development): `telegram_session_name = "dev_session"`
   - Update in database using: `python cli.py setting set telegram_session_name "prod_session"`

## Current Setup (from your code)

- Session name: `anon` (from DB setting `telegram_session_name`)
- File: `anon.session`
- Running on: DigitalOcean App Platform

## Quick Fix Commands

**On DigitalOcean (via console):**
```bash
# Delete old session
rm -f anon.session

# Regenerate
python regenerate_session.py
# Follow prompts for phone + code

# Restart the app (or it will auto-restart)
```

**On local machine (if you want to switch to local):**
```bash
# Stop any DigitalOcean instances first!
python regenerate_session.py
# Follow prompts

# Run bot
python main.py
```

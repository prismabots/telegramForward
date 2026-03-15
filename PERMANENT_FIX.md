# Permanent Fix for AuthKeyDuplicatedError on App Platform

## The Problem

When DigitalOcean App Platform restarts or changes IPs, Telegram invalidates the session. 
We can't keep regenerating and committing session files.

## The Solution

Let the bot create its own session on startup using environment variables.

## Setup Instructions

### Step 1: Set Environment Variables in DigitalOcean

1. Go to https://cloud.digitalocean.com/apps
2. Click your `telegramForward` app
3. Go to **Settings** → **App-Level Environment Variables**
4. Add these variables:

```
TELEGRAM_PHONE = +12063065720
```

(Replace with your actual phone number including country code)

**Note:** You DON'T need `TELEGRAM_CODE` unless the bot needs to authorize for the first time.

### Step 2: Update Run Command

In App Platform settings:

1. Go to **Components** → Click your worker/web service
2. Under **Run Command**, change from:
   ```
   python main.py
   ```
   to:
   ```
   bash start.sh
   ```

3. Click **Save**

### Step 3: Deploy

The changes are already in the repo. Just:

1. The app will auto-deploy when you change the run command
2. Monitor the logs

### What Happens Now

On every startup:
1. `start.sh` runs `init_session.py`
2. If session is valid → continues to `main.py`
3. If session is invalid → deletes it and creates a new one
4. If needs authorization → checks `TELEGRAM_CODE` environment variable

### First-Time Setup (If Bot Not Authorized Yet)

If the bot has never been authorized on DigitalOcean:

1. **Temporarily add** `TELEGRAM_CODE` environment variable:
   - Check your Telegram app for the code
   - Add it to environment variables
   - Let the app redeploy
   
2. **After successful login**, remove `TELEGRAM_CODE` (not needed anymore)

3. If you have 2FA enabled, also add:
   ```
   TELEGRAM_PASSWORD = your_2fa_password
   ```

### Checking Logs

In DigitalOcean → Runtime Logs, you should see:

```
Telegram Session Initializer
Session file: anon.session
✓ Session is valid and authorized
✓ Logged in as: Kyle (@nambanorm)
✓ Session ready - starting bot...
```

### Benefits

✅ No more manual session regeneration
✅ Survives IP changes and restarts  
✅ Session never committed to Git (security)
✅ Automatic recovery from AuthKeyDuplicatedError

## Troubleshooting

**"Session initialization failed"**
- Check that `TELEGRAM_PHONE` is set correctly
- If first time: Set `TELEGRAM_CODE` with verification code
- If 2FA enabled: Set `TELEGRAM_PASSWORD`

**Still getting AuthKeyDuplicatedError**
- Make sure bot is NOT running locally on your machine
- Check no other apps are using the same Telegram account

# EASY FIX - No Console Needed!

Since the DigitalOcean console isn't loading, use this method:

## Step 1: Create Session Locally (2 minutes)

Run this command:

```powershell
python simple_session_gen.py
```

When prompted, enter:
- **Telegram API ID**: (check your database or DigitalOcean environment variables)
- **Telegram API Hash**: (check your database or DigitalOcean environment variables)  
- **Session name**: Just press Enter (uses "anon")
- **Phone number**: Your phone number with country code (e.g., +1234567890)
- **Verification code**: Check your Telegram app

This creates `anon.session` in your current folder.

## Step 2: Deploy to App Platform (3 minutes)

```powershell
# Add the session file
git add anon.session

# Commit it
git commit -m "Add regenerated Telegram session"

# Push to GitHub (triggers auto-deploy)
git push origin main
```

Wait ~3 minutes for DigitalOcean to redeploy.

## Step 3: Restore Security (1 minute)

After deployment succeeds:

```powershell
# Restore gitignore protection
python restore_gitignore.py

# Commit the protection
git add .gitignore
git commit -m "Restore session file protection"
git push origin main
```

## Done! ✓

Your bot will be running with the fresh session.

---

## If You Don't Know Your API Credentials

Check DigitalOcean App Platform environment variables:
1. Go to https://cloud.digitalocean.com/apps
2. Click your app → Settings → Environment Variables
3. Look for `TELEGRAM_API_ID` and `TELEGRAM_API_HASH`

Or check your database settings table.

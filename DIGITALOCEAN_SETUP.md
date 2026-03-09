# Setting Up Automated Cleanup on DigitalOcean (Simple Method)

Since GitHub Actions can't connect to your database (firewall protected), here's the easiest way to set up automated cleanup directly on your DigitalOcean server.

## Method 1: One-Command Setup (Easiest!)

### Step 1: SSH into your DigitalOcean server

Find where your bot is running and SSH in:

```bash
ssh root@your-server-ip
# Or if you're using DigitalOcean App Platform, use their console
```

### Step 2: Create a simple cron job

Run this **ONE command** and you're done (replace YOUR_DB_CONNECTION with your actual connection string):

```bash
(crontab -l 2>/dev/null; echo "BACKUP_DB_ADMIN_URL='YOUR_DATABASE_CONNECTION_STRING'"; echo "0 2 * * 0 cd $(pwd) && /usr/bin/python3 cleanup_old_messages.py >> /var/log/telegram_cleanup.log 2>&1") | crontab -
```

That's it! The cleanup will now run every Sunday at 2 AM.

### Step 3: Verify it's installed

```bash
crontab -l
```

You should see your cleanup job listed.

### Step 4: Test it now (optional)

```bash
python3 cleanup_old_messages.py --dry-run
```

---

## Method 2: Manual Setup (If Method 1 Doesn't Work)

### Step 1: Open crontab editor

```bash
crontab -e
```

### Step 2: Add these lines at the bottom

Press `i` to enter insert mode, then paste (replace with your actual connection string):

```bash
BACKUP_DB_ADMIN_URL="YOUR_DATABASE_CONNECTION_STRING"
0 2 * * 0 cd /root/telegramForward && /usr/bin/python3 cleanup_old_messages.py >> /var/log/telegram_cleanup.log 2>&1
```

**Important:** Replace `/root/telegramForward` with the actual path where your bot code is!

### Step 3: Save and exit

- Press `ESC`
- Type `:wq`
- Press `ENTER`

---

## Checking the Logs

View what was cleaned up:

```bash
# View the log file
cat /var/log/telegram_cleanup.log

# Watch it in real-time (when running)
tail -f /var/log/telegram_cleanup.log
```

---

## What If I Can't SSH?

If you're using **DigitalOcean App Platform** and can't SSH:

### Option A: Use the Console

1. Go to your app in DigitalOcean
2. Click "Console" tab
3. Run the commands above

### Option B: Add to your bot's startup script

Add this to the end of your `main.py` or create a startup script:

```python
import subprocess
import os

# Install cron job on startup
cron_command = f"""
(crontab -l 2>/dev/null; echo "BACKUP_DB_ADMIN_URL='{os.environ.get('BACKUP_DB_ADMIN_URL')}'"; echo "0 2 * * 0 cd {os.getcwd()} && python3 cleanup_old_messages.py >> /var/log/telegram_cleanup.log 2>&1") | crontab -
"""
subprocess.run(cron_command, shell=True)
```

---

## Troubleshooting

### "crontab: command not found"

Install cron:

```bash
apt-get update && apt-get install -y cron
service cron start
```

### Check if cron is running

```bash
service cron status
```

If not running:

```bash
service cron start
```

### Manually run cleanup now

```bash
cd /path/to/telegramForward
python3 cleanup_old_messages.py
```

---

## What About GitHub Actions?

Since GitHub Actions can't connect to your database (firewall), you have two options:

1. **Use the server-based cron** (recommended - what this guide does)
2. **Whitelist GitHub's IPs** (not recommended - very long list, changes frequently)

For whitelisting GitHub IPs, you'd need to:
1. Go to DigitalOcean → Databases → Your Database → Settings → Trusted Sources
2. Add ALL of GitHub's IP ranges from: https://api.github.com/meta
3. This list has 100+ IP ranges and changes monthly

**Server-based cron is much simpler and more reliable!**

---

## Summary

✅ **Easiest:** Run the one-command setup above  
✅ **Runs:** Every Sunday at 2 AM automatically  
✅ **Secure:** Only your server can access the database  
✅ **Simple:** No GitHub Actions, no IP whitelisting needed  

Just SSH in, run one command, and you're done! 🎉

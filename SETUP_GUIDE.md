# Setting Up Automated Cleanup on DigitalOcean

Since you're using DigitalOcean App Platform, here are the easiest ways to set up automated cleanup:

## Option 1: Using DigitalOcean Console (Easiest)

### Step 1: SSH into your DigitalOcean droplet/server

```bash
ssh root@your-server-ip
```

### Step 2: Navigate to your app directory

```bash
cd /path/to/your/telegramForward
# Usually something like: cd /app or cd /home/your-user/telegramForward
```

### Step 3: Set up the environment variable

```bash
# Add to your shell profile (so it's available to cron)
echo 'export BACKUP_DB_ADMIN_URL="YOUR_DATABASE_CONNECTION_STRING"' >> ~/.bashrc
source ~/.bashrc
```

### Step 4: Test the cleanup script

```bash
# Test (won't delete anything)
python3 cleanup_old_messages.py --dry-run
```

### Step 5: Install the cron job manually

```bash
# Open crontab editor
crontab -e

# Add this line (press 'i' to insert, then paste):
BACKUP_DB_ADMIN_URL="YOUR_DATABASE_CONNECTION_STRING"
0 2 * * 0 cd /path/to/telegramForward && /usr/bin/python3 cleanup_old_messages.py >> /var/log/telegram_cleanup.log 2>&1

# Save and exit (press ESC, then type :wq and press ENTER)
```

**Replace `/path/to/telegramForward` with your actual path!**

---

## Option 2: Run Manually Whenever You Want (No Cron)

You can just run the cleanup manually whenever you want from your local Windows machine:

### On Windows (PowerShell):

```powershell
# Set the environment variable (in PowerShell)
$env:BACKUP_DB_ADMIN_URL='YOUR_DATABASE_CONNECTION_STRING'

# Preview what would be deleted
python cleanup_old_messages.py --dry-run

# Actually delete old messages
python cleanup_old_messages.py
```

Just run this once a week (or whenever you remember) and you're good!

---

## Option 3: Use GitHub Actions (Automated, No Server Access Needed)

If you don't want to SSH into the server, you can use GitHub Actions to run the cleanup automatically.

I can create a GitHub Actions workflow file that runs weekly. Would you like me to do that?

---

## Quick Manual Cleanup (Right Now)

If you just want to clean up old messages right now from your Windows machine:

```powershell
# In PowerShell (run from the telegramForward directory):
$env:BACKUP_DB_ADMIN_URL='YOUR_DATABASE_CONNECTION_STRING'
python cleanup_old_messages.py --dry-run
```

If the preview looks good, run it for real:

```powershell
python cleanup_old_messages.py
```

---

## Which Option Do You Prefer?

1. **Manual cleanup** - Run from your Windows machine whenever you want (easiest, no setup)
2. **SSH + Cron** - Set up once on DigitalOcean, runs automatically forever
3. **GitHub Actions** - I create a workflow file, GitHub runs it weekly (no SSH needed)

Let me know which you'd like and I can help you set it up!

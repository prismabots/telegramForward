# Automated Message Cleanup System

This system automatically deletes old message records from the database to keep storage manageable while preserving recent messages for reply threading functionality.

## Overview

- **What it does**: Deletes message records older than 7 days (configurable)
- **When it runs**: Every Sunday at 2:00 AM (configurable)
- **What it keeps**: Recent messages (last 7 days) for Discord reply threading
- **What it deletes**: Records in `tele_messages` table older than retention period

## Quick Start

### 1. Installation (Linux/macOS)

```bash
# Make the setup script executable
chmod +x setup_cleanup_cron.sh

# Run the setup script
bash setup_cleanup_cron.sh
```

This will:
- ✅ Make cleanup script executable
- ✅ Create log directory at `/var/log/telegram_cleanup/`
- ✅ Install weekly cron job (Sundays at 2 AM)
- ✅ Test the cleanup script

### 2. Manual Cleanup (Windows/Linux/macOS)

```bash
# Preview what would be deleted (safe to run)
python cleanup_old_messages.py --dry-run

# Actually delete old messages
python cleanup_old_messages.py

# Custom retention period (keep 14 days instead of 7)
python cleanup_old_messages.py --retention-days 14
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `BACKUP_DB_ADMIN_URL` | *(required)* | PostgreSQL connection string |
| `MESSAGE_RETENTION_DAYS` | `7` | Number of days to keep messages |

### Customizing the Schedule

Edit your crontab to change when cleanup runs:

```bash
# Open crontab editor
crontab -e

# Example schedules:
# Daily at 3 AM:     0 3 * * *
# Weekly on Monday:  0 2 * * 1
# Monthly on 1st:    0 2 1 * *
```

## Monitoring

### View Logs

```bash
# View recent cleanup logs
tail -f /var/log/telegram_cleanup/cleanup.log

# View last 50 lines
tail -50 /var/log/telegram_cleanup/cleanup.log

# Search for errors
grep ERROR /var/log/telegram_cleanup/cleanup.log
```

### Check Cron Job Status

```bash
# List all cron jobs
crontab -l

# View cron execution logs (system-specific)
grep CRON /var/log/syslog
```

## Usage Examples

### Dry Run (Preview Only)

```bash
$ python cleanup_old_messages.py --dry-run

╔════════════════════════════════════════════════════════════════╗
║               TELEGRAM MESSAGE CLEANUP SCRIPT                  ║
╚════════════════════════════════════════════════════════════════╝

🔍 DRY RUN MODE - No data will be deleted

📊 PREVIEW: Messages older than 7 days
======================================================================

📢 VIP Premium Zone
   Messages to delete: 1,234
   Oldest: 2026-02-15 08:23:45
   Newest: 2026-03-01 23:59:59

📢 France Trading Pro
   Messages to delete: 856
   Oldest: 2026-02-16 10:15:30
   Newest: 2026-03-01 22:30:15

======================================================================
📦 TOTAL: 2,090 messages would be deleted
```

### Actual Cleanup

```bash
$ python cleanup_old_messages.py

╔════════════════════════════════════════════════════════════════╗
║               TELEGRAM MESSAGE CLEANUP SCRIPT                  ║
╚════════════════════════════════════════════════════════════════╝

🗑️  Starting cleanup: messages older than 7 days
⏰ Start time: 2026-03-09 02:00:00
======================================================================
✅ VIP Premium Zone: Deleted 1,234 messages
✅ France Trading Pro: Deleted 856 messages
✅ ADK: Deleted 423 messages

======================================================================
✅ Cleanup complete!
📦 Total deleted: 2,513 messages
⏱️  Duration: 1.23 seconds
⏰ End time: 2026-03-09 02:00:01
```

### Custom Retention Period

```bash
# Keep messages for 14 days instead of 7
python cleanup_old_messages.py --retention-days 14

# Or set environment variable
export MESSAGE_RETENTION_DAYS=14
python cleanup_old_messages.py
```

## Troubleshooting

### Script Doesn't Run Automatically

1. **Check if cron service is running:**
   ```bash
   sudo systemctl status cron  # or 'crond' on some systems
   ```

2. **Verify cron job is installed:**
   ```bash
   crontab -l | grep cleanup
   ```

3. **Check environment variables in cron:**
   ```bash
   # Add to crontab (crontab -e)
   BACKUP_DB_ADMIN_URL=postgresql://...
   0 2 * * 0 cd /path/to/telegramForward && python3 cleanup_old_messages.py
   ```

### Database Connection Errors

1. **Check environment variable:**
   ```bash
   echo $BACKUP_DB_ADMIN_URL
   ```

2. **Test connection manually:**
   ```bash
   python cleanup_old_messages.py --dry-run
   ```

3. **Verify database is accessible:**
   ```bash
   psql $BACKUP_DB_ADMIN_URL -c "SELECT COUNT(*) FROM tele_messages;"
   ```

### Permission Errors

```bash
# Make script executable
chmod +x cleanup_old_messages.py

# Create log directory with proper permissions
sudo mkdir -p /var/log/telegram_cleanup
sudo chown $(whoami):$(whoami) /var/log/telegram_cleanup
```

## Safety Features

✅ **Transaction-based**: All deletions happen in a single transaction (rollback on error)  
✅ **Dry-run mode**: Preview deletions before committing  
✅ **Detailed logging**: Track what was deleted and when  
✅ **Error handling**: Graceful failure with clear error messages  
✅ **Configurable retention**: Easily adjust how long to keep messages  

## Database Impact

- **Storage savings**: Typically reduces database size by 70-90% after first run
- **Performance**: Improves query speed on `tele_messages` table
- **Reply threading**: Recent messages (last 7 days) preserved for Discord replies
- **Execution time**: ~1-5 seconds for typical workloads

## Uninstallation

```bash
# Remove cron job
crontab -e
# Delete the line containing 'cleanup_old_messages.py'

# Or remove all cron jobs related to cleanup
crontab -l | grep -v cleanup_old_messages | crontab -

# Remove log directory (optional)
sudo rm -rf /var/log/telegram_cleanup
```

## Support

For issues or questions:
1. Check logs: `/var/log/telegram_cleanup/cleanup.log`
2. Run dry-run: `python cleanup_old_messages.py --dry-run`
3. Check database connection: `echo $BACKUP_DB_ADMIN_URL`

# PowerShell script to set up automated cleanup on DigitalOcean server
# Run this script locally - it will SSH in and configure everything

$SERVER = "root@45.55.70.214"

# Get DB URL from environment or prompt
if (-not $env:BACKUP_DB_ADMIN_URL) {
    Write-Host "❌ ERROR: BACKUP_DB_ADMIN_URL environment variable not set!" -ForegroundColor Red
    Write-Host "Set it with: `$env:BACKUP_DB_ADMIN_URL='your_connection_string'" -ForegroundColor Yellow
    exit 1
}
$DB_URL = $env:BACKUP_DB_ADMIN_URL

Write-Host "🚀 Setting up automated message cleanup on DigitalOcean server..." -ForegroundColor Cyan
Write-Host ""

# SSH command to run on the server
$sshCommand = @"
cd /root/telegramForward && \
git pull && \
(crontab -l 2>/dev/null; echo "BACKUP_DB_ADMIN_URL='$DB_URL'"; echo "0 2 * * 0 cd `$(pwd) && /usr/bin/python3 cleanup_old_messages.py >> /var/log/telegram_cleanup.log 2>&1") | crontab - && \
echo "✅ Cron job installed!" && \
echo "" && \
echo "📅 Current crontab:" && \
crontab -l && \
echo "" && \
echo "🧪 Testing cleanup script (dry-run):" && \
python3 cleanup_old_messages.py --dry-run
"@

Write-Host "Connecting to $SERVER..." -ForegroundColor Yellow
ssh $SERVER $sshCommand

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✅ Setup complete! Automated cleanup will run every Sunday at 2 AM." -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "❌ Setup failed. Please check the error message above." -ForegroundColor Red
}

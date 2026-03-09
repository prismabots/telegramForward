# Manual Cleanup Script for Windows
# Run this whenever you want to clean up old messages (recommended: weekly)

# Set your database connection string here (or set BACKUP_DB_ADMIN_URL environment variable)
if (-not $env:BACKUP_DB_ADMIN_URL) {
    Write-Host "❌ ERROR: BACKUP_DB_ADMIN_URL environment variable not set!" -ForegroundColor Red
    Write-Host "Set it with: `$env:BACKUP_DB_ADMIN_URL='your_connection_string'" -ForegroundColor Yellow
    exit 1
}

Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║         Telegram Message Cleanup - Manual Run                 ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Preview mode first
Write-Host "🔍 Running preview (dry-run)..." -ForegroundColor Yellow
python cleanup_old_messages.py --dry-run

Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
Write-Host ""

$confirmation = Read-Host "Do you want to DELETE these messages? (yes/no)"

if ($confirmation -eq "yes") {
    Write-Host ""
    Write-Host "🗑️  Deleting old messages..." -ForegroundColor Yellow
    python cleanup_old_messages.py
    Write-Host ""
    Write-Host "✅ Cleanup complete!" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "❌ Cleanup cancelled." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "💡 Tip: Run this script weekly to keep your database clean!" -ForegroundColor Cyan
Write-Host ""

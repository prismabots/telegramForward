# Automated cleanup runner (called by Windows Task Scheduler)
# DO NOT run this manually - use run_cleanup.ps1 instead

# Get DB URL from environment variable (set by Windows Task Scheduler or system)
if (-not $env:BACKUP_DB_ADMIN_URL) {
    Write-Host "ERROR: BACKUP_DB_ADMIN_URL not set!" > "$PSScriptRoot\cleanup_auto.log"
    exit 1
}

Set-Location $PSScriptRoot
python cleanup_old_messages.py *>> cleanup_auto.log

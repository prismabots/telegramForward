# Windows Task Scheduler Setup for Automated Cleanup
# This creates a scheduled task that runs every Sunday at 2 AM automatically

param(
    [string]$DBConnectionString = $env:BACKUP_DB_ADMIN_URL
)

if (-not $DBConnectionString) {
    Write-Host "❌ ERROR: Database connection string required!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Usage:" -ForegroundColor Yellow
    Write-Host '  .\setup_windows_task.ps1 "postgresql://your-connection-string"' -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Or set environment variable:" -ForegroundColor Yellow
    Write-Host '  $env:BACKUP_DB_ADMIN_URL="your-connection-string"' -ForegroundColor Cyan
    Write-Host '  .\setup_windows_task.ps1' -ForegroundColor Cyan
    exit 1
}

Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║     Windows Task Scheduler - Automated Cleanup Setup          ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Get the current directory (where the script is)
$scriptDir = $PSScriptRoot
if (-not $scriptDir) {
    $scriptDir = Get-Location
}

$cleanupScript = Join-Path $scriptDir "cleanup_old_messages.py"
$pythonExe = (Get-Command python).Source

Write-Host "📁 Script directory: $scriptDir" -ForegroundColor Gray
Write-Host "🐍 Python executable: $pythonExe" -ForegroundColor Gray
Write-Host ""

# Create the PowerShell script that will be called by Task Scheduler
$taskScriptPath = Join-Path $scriptDir "scheduled_cleanup_task.ps1"
$taskScriptContent = @"
# Auto-generated script for Windows Task Scheduler
# This runs the cleanup automatically

`$env:BACKUP_DB_ADMIN_URL = '$DBConnectionString'
Set-Location '$scriptDir'
& '$pythonExe' cleanup_old_messages.py >> '$scriptDir\cleanup.log' 2>&1
"@

Set-Content -Path $taskScriptPath -Value $taskScriptContent
Write-Host "✅ Created task script: $taskScriptPath" -ForegroundColor Green

# Create the scheduled task
$taskName = "TelegramMessageCleanup"
$taskDescription = "Automatically deletes Telegram message records older than 7 days"

# Check if task already exists
$existingTask = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if ($existingTask) {
    Write-Host "⚠️  Task '$taskName' already exists. Removing..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
}

# Create the action (what to run)
$action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-ExecutionPolicy Bypass -File `"$taskScriptPath`"" `
    -WorkingDirectory $scriptDir

# Create the trigger (when to run) - Every Sunday at 2:00 AM
$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Sunday -At 2am

# Create the principal (run whether user is logged in or not)
$principal = New-ScheduledTaskPrincipal `
    -UserId $env:USERNAME `
    -LogonType S4U `
    -RunLevel Highest

# Create the settings
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable

# Register the task
Register-ScheduledTask `
    -TaskName $taskName `
    -Description $taskDescription `
    -Action $action `
    -Trigger $trigger `
    -Principal $principal `
    -Settings $settings | Out-Null

Write-Host ""
Write-Host "✅ Scheduled task created successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Task Details:" -ForegroundColor Cyan
Write-Host "   Name: $taskName" -ForegroundColor White
Write-Host "   Schedule: Every Sunday at 2:00 AM" -ForegroundColor White
Write-Host "   Action: Run cleanup_old_messages.py" -ForegroundColor White
Write-Host "   Log: $scriptDir\cleanup.log" -ForegroundColor White
Write-Host ""

# Test the task
Write-Host "🧪 Testing the cleanup script now..." -ForegroundColor Yellow
Write-Host ""
& $pythonExe $cleanupScript --dry-run

Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║                    Setup Complete! ✅                          ║" -ForegroundColor Green
Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""
Write-Host "📅 The cleanup will now run automatically every Sunday at 2 AM!" -ForegroundColor Cyan
Write-Host ""
Write-Host "💡 Useful commands:" -ForegroundColor Cyan
Write-Host "   • View task: Get-ScheduledTask -TaskName '$taskName'" -ForegroundColor White
Write-Host "   • Run now:   Start-ScheduledTask -TaskName '$taskName'" -ForegroundColor White
Write-Host "   • View log:  Get-Content '$scriptDir\cleanup.log'" -ForegroundColor White
Write-Host "   • Remove:    Unregister-ScheduledTask -TaskName '$taskName'" -ForegroundColor White
Write-Host ""

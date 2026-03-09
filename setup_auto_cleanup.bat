@echo off
REM Simple Windows Task Scheduler Setup
REM Run this as Administrator
REM 
REM BEFORE RUNNING: Edit this file and set your BACKUP_DB_ADMIN_URL below

echo.
echo ========================================================
echo   Setting up Automated Weekly Cleanup
echo ========================================================
echo.

REM TODO: Replace YOUR_DB_CONNECTION_STRING with your actual connection string
set DB_URL=YOUR_DB_CONNECTION_STRING

if "%DB_URL%"=="YOUR_DB_CONNECTION_STRING" (
    echo [ERROR] You must edit this file and set your database connection string first!
    echo Edit setup_auto_cleanup.bat and replace YOUR_DB_CONNECTION_STRING
    pause
    exit /b 1
)

REM Set the environment variable permanently (system-wide)
echo Setting database connection environment variable...
setx BACKUP_DB_ADMIN_URL "%DB_URL%" /M

REM Create the cleanup task
schtasks /create /tn "TelegramMessageCleanup" /tr "powershell.exe -ExecutionPolicy Bypass -File \"%~dp0run_cleanup_auto.ps1\"" /sc weekly /d SUN /st 02:00 /f /rl HIGHEST

if %ERRORLEVEL% EQU 0 (
    echo.
    echo [SUCCESS] Scheduled task created!
    echo.
    echo The cleanup will run every Sunday at 2:00 AM automatically.
    echo.
    echo Useful commands:
    echo   - Run now:    schtasks /run /tn "TelegramMessageCleanup"
    echo   - View task:  schtasks /query /tn "TelegramMessageCleanup" /v
    echo   - Delete:     schtasks /delete /tn "TelegramMessageCleanup" /f
    echo.
) else (
    echo.
    echo [ERROR] Failed to create task. Make sure you run this as Administrator!
    echo.
)

pause

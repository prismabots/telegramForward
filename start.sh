#!/bin/bash
# Startup script for DigitalOcean App Platform
# This ensures session is valid before starting the bot

echo "Starting Telegram Forward Bot..."
echo ""

# Initialize/validate session
python init_session.py
SESSION_RESULT=$?

if [ $SESSION_RESULT -ne 0 ]; then
    echo ""
    echo "Session initialization failed!"
    echo "Please check environment variables:"
    echo "  - TELEGRAM_PHONE (required for first setup)"
    echo "  - TELEGRAM_CODE (required if not authorized)"
    echo "  - TELEGRAM_PASSWORD (required if 2FA enabled)"
    echo ""
    exit 1
fi

echo ""
echo "Starting main bot application..."
python main.py

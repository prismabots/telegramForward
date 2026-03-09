#!/bin/bash
#
# Setup script for automated message cleanup cron job
#
# This script installs a weekly cron job that runs cleanup_old_messages.py
# every Sunday at 2:00 AM to delete message records older than 7 days.
#
# Usage:
#   bash setup_cleanup_cron.sh
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║         Telegram Message Cleanup - Cron Setup Script          ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
CLEANUP_SCRIPT="$SCRIPT_DIR/cleanup_old_messages.py"

# Check if cleanup script exists
if [ ! -f "$CLEANUP_SCRIPT" ]; then
    echo -e "${RED}❌ ERROR: cleanup_old_messages.py not found at $CLEANUP_SCRIPT${NC}"
    exit 1
fi

# Make cleanup script executable
chmod +x "$CLEANUP_SCRIPT"
echo -e "${GREEN}✅ Made cleanup script executable${NC}"

# Check if BACKUP_DB_ADMIN_URL is set
if [ -z "$BACKUP_DB_ADMIN_URL" ]; then
    echo -e "${YELLOW}⚠️  WARNING: BACKUP_DB_ADMIN_URL environment variable not set${NC}"
    echo -e "${YELLOW}   Make sure to set it in your environment or crontab${NC}"
fi

# Get Python path
PYTHON_PATH=$(which python3 || which python)
echo -e "${BLUE}📍 Python path: $PYTHON_PATH${NC}"

# Create log directory
LOG_DIR="/var/log/telegram_cleanup"
if [ ! -d "$LOG_DIR" ]; then
    echo -e "${YELLOW}📁 Creating log directory: $LOG_DIR${NC}"
    sudo mkdir -p "$LOG_DIR"
    sudo chown $(whoami):$(whoami) "$LOG_DIR"
    echo -e "${GREEN}✅ Log directory created${NC}"
fi

# Create cron job entry
CRON_SCHEDULE="0 2 * * 0"  # Every Sunday at 2:00 AM
CRON_JOB="$CRON_SCHEDULE cd $SCRIPT_DIR && $PYTHON_PATH $CLEANUP_SCRIPT >> $LOG_DIR/cleanup.log 2>&1"

echo ""
echo -e "${BLUE}📋 Cron job configuration:${NC}"
echo -e "   Schedule: ${GREEN}Every Sunday at 2:00 AM${NC}"
echo -e "   Script: $CLEANUP_SCRIPT"
echo -e "   Log: $LOG_DIR/cleanup.log"
echo ""

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "$CLEANUP_SCRIPT"; then
    echo -e "${YELLOW}⚠️  Cron job for cleanup script already exists${NC}"
    echo -e "${YELLOW}   Removing old entry...${NC}"
    crontab -l | grep -v "$CLEANUP_SCRIPT" | crontab -
fi

# Add cron job
echo -e "${GREEN}➕ Adding cron job...${NC}"
(crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -

echo -e "${GREEN}✅ Cron job installed successfully!${NC}"
echo ""

# Display current crontab
echo -e "${BLUE}📅 Current crontab:${NC}"
crontab -l | tail -3
echo ""

# Test the script
echo -e "${BLUE}🧪 Testing cleanup script (dry-run)...${NC}"
if $PYTHON_PATH "$CLEANUP_SCRIPT" --dry-run; then
    echo -e "${GREEN}✅ Test successful!${NC}"
else
    echo -e "${RED}❌ Test failed - check your database connection${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                    Setup Complete! ✅                          ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}📝 Next steps:${NC}"
echo -e "   1. Cleanup will run automatically every Sunday at 2:00 AM"
echo -e "   2. Check logs at: $LOG_DIR/cleanup.log"
echo -e "   3. Run manual cleanup: ${GREEN}python3 $CLEANUP_SCRIPT${NC}"
echo -e "   4. Preview before deletion: ${GREEN}python3 $CLEANUP_SCRIPT --dry-run${NC}"
echo ""
echo -e "${BLUE}💡 Tips:${NC}"
echo -e "   - Change retention period: ${GREEN}export MESSAGE_RETENTION_DAYS=14${NC}"
echo -e "   - View cron jobs: ${GREEN}crontab -l${NC}"
echo -e "   - Remove cron job: ${GREEN}crontab -e${NC} (then delete the line)"
echo ""

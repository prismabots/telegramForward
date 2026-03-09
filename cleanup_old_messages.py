#!/usr/bin/env python3
"""
Automated cleanup script for old Telegram message records.

Deletes message records older than the configured retention period (default: 7 days).
This keeps the database size manageable while preserving recent messages for reply threading.

Usage:
    python cleanup_old_messages.py              # Run cleanup
    python cleanup_old_messages.py --dry-run    # Preview what would be deleted
    
Environment Variables:
    BACKUP_DB_ADMIN_URL: PostgreSQL connection string (required)
    MESSAGE_RETENTION_DAYS: Number of days to keep messages (default: 7)
"""

import os
import sys
import psycopg2
from datetime import datetime, timedelta
import argparse


def get_db_connection():
    """Get database connection from environment variable."""
    conn_string = os.environ.get("BACKUP_DB_ADMIN_URL")
    if not conn_string:
        print("❌ ERROR: BACKUP_DB_ADMIN_URL environment variable not set!")
        sys.exit(1)
    
    try:
        return psycopg2.connect(conn_string)
    except Exception as e:
        print(f"❌ ERROR: Failed to connect to database: {e}")
        sys.exit(1)


def preview_cleanup(conn, retention_days):
    """Show what would be deleted without actually deleting."""
    print(f"\n📊 PREVIEW: Messages older than {retention_days} days")
    print("=" * 70)
    
    cur = conn.cursor()
    
    # Get summary by channel
    cur.execute("""
        SELECT 
            tc.name as channel_name,
            COUNT(tm.id) as message_count,
            MIN(tm.created_at) as oldest_message,
            MAX(tm.created_at) as newest_old_message
        FROM tele_messages tm
        JOIN tele_channels tc ON tm.channel_id = tc.id
        WHERE tm.created_at < NOW() - INTERVAL '%s days'
        GROUP BY tc.name
        ORDER BY message_count DESC
    """, (retention_days,))
    
    results = cur.fetchall()
    
    if not results:
        print("✅ No messages to delete!")
        cur.close()
        return 0
    
    total_count = 0
    for channel_name, count, oldest, newest in results:
        print(f"\n📢 {channel_name}")
        print(f"   Messages to delete: {count:,}")
        print(f"   Oldest: {oldest}")
        print(f"   Newest: {newest}")
        total_count += count
    
    print("\n" + "=" * 70)
    print(f"📦 TOTAL: {total_count:,} messages would be deleted")
    
    cur.close()
    return total_count


def cleanup_old_messages(conn, retention_days, dry_run=False):
    """Delete messages older than retention_days."""
    start_time = datetime.now()
    
    print(f"\n🗑️  Starting cleanup: messages older than {retention_days} days")
    print(f"⏰ Start time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    if dry_run:
        print("🔍 DRY RUN MODE - No data will be deleted")
        total_deleted = preview_cleanup(conn, retention_days)
        print("\n✅ Dry run complete!")
        return total_deleted
    
    cur = conn.cursor()
    
    try:
        # Delete old messages and capture details
        cur.execute("""
            WITH deleted AS (
                DELETE FROM tele_messages
                WHERE created_at < NOW() - INTERVAL '%s days'
                RETURNING channel_id, id, created_at
            )
            SELECT 
                tc.name as channel_name,
                COUNT(d.id) as deleted_count
            FROM deleted d
            JOIN tele_channels tc ON d.channel_id = tc.id
            GROUP BY tc.name
            ORDER BY deleted_count DESC
        """, (retention_days,))
        
        results = cur.fetchall()
        conn.commit()
        
        if not results:
            print("✅ No old messages found to delete!")
            cur.close()
            return 0
        
        total_deleted = 0
        for channel_name, count in results:
            print(f"✅ {channel_name}: Deleted {count:,} messages")
            total_deleted += count
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print("\n" + "=" * 70)
        print(f"✅ Cleanup complete!")
        print(f"📦 Total deleted: {total_deleted:,} messages")
        print(f"⏱️  Duration: {duration:.2f} seconds")
        print(f"⏰ End time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        cur.close()
        return total_deleted
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ ERROR during cleanup: {e}")
        cur.close()
        raise


def main():
    parser = argparse.ArgumentParser(
        description="Cleanup old Telegram message records from database"
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview what would be deleted without actually deleting'
    )
    parser.add_argument(
        '--retention-days',
        type=int,
        default=None,
        help='Number of days to keep messages (overrides env var)'
    )
    
    args = parser.parse_args()
    
    # Get retention period
    retention_days = args.retention_days or int(os.environ.get("MESSAGE_RETENTION_DAYS", "7"))
    
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 15 + "TELEGRAM MESSAGE CLEANUP SCRIPT" + " " * 21 + "║")
    print("╚" + "═" * 68 + "╝")
    
    # Connect to database
    conn = get_db_connection()
    
    try:
        # Run cleanup
        deleted_count = cleanup_old_messages(conn, retention_days, dry_run=args.dry_run)
        
        if not args.dry_run:
            # Log to system log if available
            log_message = f"Telegram cleanup: Deleted {deleted_count} messages older than {retention_days} days"
            print(f"\n📝 {log_message}")
        
    except Exception as e:
        print(f"\n❌ FATAL ERROR: {e}")
        sys.exit(1)
    finally:
        conn.close()
    
    print("\n" + "=" * 70)
    print("👋 Cleanup script finished\n")


if __name__ == "__main__":
    main()

import psycopg2
import os

conn_string = os.environ.get('BACKUP_DB_ADMIN_URL')
if not conn_string:
    print("ERROR: BACKUP_DB_ADMIN_URL not set")
    exit(1)

try:
    # Single connection, not using the pool
    conn = psycopg2.connect(conn_string, connect_timeout=5)
    cur = conn.cursor()
    
    # Get all settings
    cur.execute("SELECT key, value FROM tele_settings ORDER BY key")
    rows = cur.fetchall()
    
    print("\n╔════════════════════════════════════════════════════════════╗")
    print("║              Settings in Database                          ║")
    print("╚════════════════════════════════════════════════════════════╝\n")
    
    for key, value in rows:
        # Mask sensitive values
        if 'api' in key.lower() or 'hash' in key.lower() or 'token' in key.lower():
            display_value = value[:4] + "..." + value[-4:] if len(value) > 8 else "***"
        else:
            display_value = value
        
        print(f"  {key:30} = {display_value}")
    
    print(f"\n  Total settings: {len(rows)}\n")
    
    cur.close()
    conn.close()
    
except psycopg2.OperationalError as e:
    print(f"\n❌ Database connection error: {e}")
    print("\nThis usually means:")
    print("  - Your bot is using all available database connections")
    print("  - You may need to restart the bot or increase connection limit")
    print("\nTo view settings, use DigitalOcean database console instead.")
except Exception as e:
    print(f"\n❌ Error: {e}")

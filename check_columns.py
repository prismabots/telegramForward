#!/usr/bin/env python3
"""Check if fallback columns exist in database."""
import db
import psycopg2

conn = db.get_connection()
try:
    with conn.cursor() as cur:
        # Check if columns exist
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'tele_channels'
            ORDER BY column_name
        """)
        columns = [row[0] for row in cur.fetchall()]
        
        print("Columns in tele_channels table:")
        for col in sorted(columns):
            marker = "✓" if col.startswith("ai_fallback") else " "
            print(f"  {marker} {col}")
        
        print()
        if "ai_fallback_provider" in columns:
            print("✓ Fallback columns EXIST")
        else:
            print("✗ Fallback columns DO NOT EXIST - migrations may not have run")
            print()
            print("Run this to add them:")
            print("  python -c \"import db; db.init_db()\"")
        
        # Also check actual data
        print()
        print("Sample channel fallback data:")
        cur.execute("SELECT name, ai_fallback_provider, ai_fallback_model FROM tele_channels LIMIT 3")
        for row in cur.fetchall():
            print(f"  {row[0]:30s} | fallback_provider: {row[1]} | fallback_model: {row[2]}")
            
finally:
    db.release_connection(conn)

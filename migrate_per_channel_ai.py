"""
Add per-channel AI model configuration columns to tele_channels table
"""
import db
from load_env import load_environment

load_environment()

SQL_MIGRATION = """
-- Add ai_provider column (per-channel AI provider override)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'tele_channels' AND column_name = 'ai_provider'
    ) THEN
        ALTER TABLE tele_channels ADD COLUMN ai_provider TEXT;
    END IF;
END $$;

-- Add ai_model column (per-channel AI model override)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'tele_channels' AND column_name = 'ai_model'
    ) THEN
        ALTER TABLE tele_channels ADD COLUMN ai_model TEXT;
    END IF;
END $$;
"""

print("\n" + "="*70)
print("ADDING PER-CHANNEL AI MODEL CONFIGURATION")
print("="*70)

try:
    conn = db.get_connection()
    with conn.cursor() as cur:
        cur.execute(SQL_MIGRATION)
        conn.commit()
    db.release_connection(conn)
    
    print("\n✅ Migration completed successfully!")
    print("\nAdded columns to tele_channels:")
    print("  • ai_provider  - Override global AI provider per channel")
    print("  • ai_model     - Override global AI model per channel")
    
    print("\n" + "="*70)
    print("HOW IT WORKS")
    print("="*70)
    print("\nIf channel has these columns set (not NULL):")
    print("  → Use channel-specific provider/model")
    print("  → API keys come from environment (X_API_KEY, OPENAI_API_KEY, etc.)")
    print("\nIf channel columns are NULL:")
    print("  → Fall back to global settings (ai_provider, ai_model from tele_settings)")
    
    print("\n" + "="*70)
    print("EXAMPLE")
    print("="*70)
    print("\nChannel 13 (SPX Options):")
    print("  ai_provider: grok")
    print("  ai_model: grok-4-1-fast-reasoning")
    print("  Uses: X_API_KEY from environment")
    print("\nChannel 3 (VIP Premium Zone - Crypto/Forex):")
    print("  ai_provider: glm")
    print("  ai_model: glm-4-flash")
    print("  Uses: GLM_API_KEY from environment")
    
    print("\n" + "="*70)
    print("NEXT STEPS")
    print("="*70)
    print("\n1. Update code to check channel-specific settings first")
    print("2. Set GLM model for Crypto/Forex channels")
    print("3. Keep Grok for SPX Options (channel 13)")
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    exit(1)

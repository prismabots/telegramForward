"""
load_env.py — Load environment variables from .env file

This helper script loads credentials from .env file into environment variables.
Use this at the start of any script that needs database or API access.

Usage:
    from load_env import load_environment
    load_environment()
"""

import os
from pathlib import Path


def load_environment():
    """Load environment variables from .env file if it exists."""
    
    # Find .env file in project root
    env_file = Path(__file__).parent / ".env"
    
    if not env_file.exists():
        print("⚠️  No .env file found. Using system environment variables.")
        return False
    
    # Read and parse .env file
    with open(env_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            
            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue
            
            # Parse KEY=VALUE
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                
                # Only set if not already in environment
                if key and not os.environ.get(key):
                    os.environ[key] = value
    
    print("✅ Environment variables loaded from .env")
    return True


def verify_credentials():
    """Verify that required credentials are present."""
    
    required = {
        'BACKUP_DB_ADMIN_URL': 'Database connection string',
        'OPENAI_API_KEY': 'OpenAI API key'
    }
    
    missing = []
    
    for key, description in required.items():
        value = os.environ.get(key)
        if not value:
            missing.append(f"  - {key} ({description})")
        else:
            # Show masked version
            if len(value) > 20:
                masked = value[:10] + '...' + value[-4:]
            else:
                masked = '***'
            print(f"✅ {key}: {masked}")
    
    if missing:
        print("\n❌ Missing credentials:")
        for item in missing:
            print(item)
        return False
    
    return True


# Auto-load when imported
if __name__ != "__main__":
    load_environment()


# If run directly, verify credentials
if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("ENVIRONMENT VERIFICATION")
    print("=" * 60 + "\n")
    
    load_environment()
    print()
    
    if verify_credentials():
        print("\n✅ All required credentials are present!")
    else:
        print("\n❌ Some credentials are missing. Please check .env file.")
    
    print("\n" + "=" * 60)

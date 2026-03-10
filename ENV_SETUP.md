# Environment Setup - Credentials Management

## Overview

This project uses a `.env` file to store sensitive credentials locally. This file is **git-ignored** and will never be pushed to GitHub.

## Files

### `.env` (Git-Ignored ✅)
Contains your actual credentials:
- `BACKUP_DB_ADMIN_URL` - PostgreSQL database connection string
- `OPENAI_API_KEY` - OpenAI API key for AI processing

**Location:** `c:\Users\User\Documents\GitHub\telegramForward\.env`

### `load_env.py`
Helper script to automatically load credentials from `.env` file.

## Usage

### Method 1: Auto-Load (Recommended)

Simply import the module at the top of your script:

```python
from load_env import load_environment

# This loads credentials automatically
load_environment()

# Now you can use the environment variables
import os
db_url = os.environ.get("BACKUP_DB_ADMIN_URL")
api_key = os.environ.get("OPENAI_API_KEY")
```

### Method 2: Verify Credentials

Run the verification script:

```powershell
python load_env.py
```

This will show you which credentials are loaded (with masked values).

## Quick Start

All test scripts can now work without manually setting environment variables:

```powershell
# Just run any test script directly
python test_algo_pro_fresh.py
python test_real_messages.py
python test_spx_options_prompts.py

# Or apply configurations
python apply_spx_options_prompts.py
python apply_algo_pro_prompts.py
python apply_forex_gold_ai.py
```

The credentials will be loaded automatically!

## Security

✅ **Safe:**
- `.env` is listed in `.gitignore`
- File will never be committed to GitHub
- Credentials stay on your local machine

❌ **Never:**
- Commit `.env` to git
- Share `.env` file
- Copy credentials into code files
- Push credentials to GitHub

## Verification

To check if your credentials are properly set up:

```powershell
python load_env.py
```

Expected output:
```
✅ Environment variables loaded from .env
✅ BACKUP_DB_ADMIN_URL: postgresql...uire
✅ OPENAI_API_KEY: sk-proj-Kj...Di8A
✅ All required credentials are present!
```

## Troubleshooting

### "No .env file found"
**Solution:** The `.env` file is created. Make sure you're in the correct directory:
```powershell
cd c:\Users\User\Documents\GitHub\telegramForward
```

### "Missing credentials"
**Solution:** Check that `.env` contains both:
- BACKUP_DB_ADMIN_URL=...
- OPENAI_API_KEY=...

### Scripts not finding credentials
**Solution:** Add this line at the top of your script:
```python
from load_env import load_environment
load_environment()
```

## For New Machines

When setting up on a new machine:

1. **Clone the repository** (credentials won't be included)
2. **Create `.env` file** manually with your credentials
3. **Run verification:**
   ```powershell
   python load_env.py
   ```

## Production Deployment (DigitalOcean)

On DigitalOcean App Platform, credentials are set via environment variables in the platform UI, not via `.env` file. The app will automatically use those instead.

---

**Note:** The `.env` file is already created with your current credentials and is ready to use!

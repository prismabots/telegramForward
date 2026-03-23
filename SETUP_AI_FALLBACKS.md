# AI Fallback System - Deployment & Setup Guide

## Problem Statement

On Mar 23, when the Grok AI provider experienced an outage, **all message processing across all 12 channels failed simultaneously**. This was a critical failure: the system had a single point of failure at the AI provider level.

**Root cause**: No fallback mechanism when primary provider became unavailable.

## Solution

Implemented a multi-provider fallback system that automatically retries with a backup provider if the primary one fails. This ensures:

- ✅ Messages are NEVER silently discarded due to provider failures
- ✅ System continues operating even when primary provider is down
- ✅ Fallback attempts are logged for monitoring
- ✅ Each channel can have independent fallback strategies

## Quick Start

### 1. Deploy Code to App Platform

```bash
git push origin main
# App Platform auto-deploys on push
```

The deployment includes:
- Updated `db.py` with new fallback columns
- Updated `ai_services.py` with fallback logic
- Updated `main.py` to use fallback configuration
- New `setup_ai_fallbacks.py` script

### 2. Initialize Database Schema

The new columns are added automatically on next deployment:
- `ai_fallback_provider` (TEXT, nullable)
- `ai_fallback_model` (TEXT, nullable)

This happens via idempotent migrations in `db.py`, so existing data is preserved.

### 3. Configure Fallback Providers

#### Option A: Automatic Setup (Recommended)

```bash
python setup_ai_fallbacks.py --dry-run
```

This shows what will be configured:

```
⚙ 'SPX Options AI' (ID 14): Provider='grok', setting fallback=glm
  [DRY-RUN] Would set: ai_fallback_provider='glm', ai_fallback_model='glm-4.7-flashx'

⚙ 'Algo Pro' (ID 13): Provider='glm', setting fallback=openai
  [DRY-RUN] Would set: ai_fallback_provider='openai', ai_fallback_model='gpt-5-nano'
```

Apply the configuration:

```bash
python setup_ai_fallbacks.py
```

Output:
```
✓ Summary: 12 channels updated, 0 skipped
```

#### Option B: Manual Configuration

For specific channels, use CLI:

```bash
python cli.py channel update 14 --fallback-provider glm --fallback-model glm-4.7-flashx
```

Or direct database:

```sql
UPDATE tele_channels 
SET ai_fallback_provider = 'glm',
    ai_fallback_model = 'glm-4.7-flashx'
WHERE id = 14;
```

### 4. Verify Configuration

Check that all AI-enabled channels have fallback providers:

```sql
SELECT id, name, ai_provider, ai_fallback_provider, ai_fallback_model
FROM tele_channels
WHERE ai_enabled = TRUE
ORDER BY id;
```

Expected output:
```
id  | name              | ai_provider | ai_fallback_provider | ai_fallback_model
----|-------------------|-------------|----------------------|------------------
13  | Algo Pro          | glm         | openai              | gpt-5-nano
14  | SPX Options AI    | grok        | glm                 | glm-4.7-flashx
15  | Forex Gold        | glm         | openai              | gpt-5-nano
... (10 more channels)
```

### 5. Verify API Keys

Ensure all required API keys are set in DigitalOcean environment:

```
X_API_KEY          = sk-...      (Grok)
GLM_API_KEY        = ...         (Zhipu AI)
OPENAI_API_KEY     = sk-...      (OpenAI)
```

If a fallback provider's key is missing, that fallback will be skipped (logged as warning).

## Testing the System

### Test 1: Simulate Primary Provider Failure

To verify fallback works, you can temporarily block the primary provider:

```python
# In ai_services.py, temporarily modify _query_grok() to raise an error:
async def _query_grok(...):
    raise Exception("Simulating Grok failure")
```

Then send a test message to a Grok-enabled channel. Expected behavior:
- Primary (Grok) fails
- Fallback (GLM) succeeds
- Message is processed and sent to Discord
- Logs show: "Falling back to glm for triage"

### Test 2: Check Logs for Fallback Usage

Deploy the system and monitor logs:

```bash
# View recent logs
doctl apps logs <app-id> --follow

# Look for fallback messages like:
# WARNING: AI triage error for 'SPX Options AI' [grok]: Connection timeout
# INFO: [SPX Options AI] Falling back to glm for triage
```

### Test 3: Verify All API Keys Work

```bash
python -c "
from ai_services import _query_openai, _query_glm, _query_grok
import asyncio
import aiohttp

async def test():
    async with aiohttp.ClientSession() as session:
        # Test each provider
        print('OpenAI:', await _query_openai(session, 'test', 'test', 'gpt-5-nano', os.environ['OPENAI_API_KEY']))
        print('GLM:', await _query_glm(session, 'test', 'test', 'glm-4.7-flashx', os.environ['GLM_API_KEY']))
        # etc.

asyncio.run(test())
"
```

## Current Configuration (After Setup)

### SPX Options AI (Primary: Grok)

```
Primary:  Grok / grok-4.1-fast
Fallback: GLM / glm-4.7-flashx
```

Behavior:
1. Grok available → Process with Grok (premium quality, <2min response time)
2. Grok fails (timeout/error) → Process with GLM (cost-effective, <30sec response time)
3. Both fail → Forward unprocessed (with error logged)

### Algo Pro AI (Primary: GLM)

```
Primary:  GLM / glm-4.7-flashx
Fallback: OpenAI / gpt-5-nano
```

### 11 Trading Signal Channels (Primary: GLM)

```
Primary:  GLM / glm-4.7-flashx
Fallback: OpenAI / gpt-5-nano
```

## Monitoring & Alerts

### What to Monitor

1. **Fallback Usage Rate**
   ```sql
   -- Check logs for fallback trigger count per day
   SELECT DATE(created_at), channel_id, COUNT(*)
   FROM log_entries
   WHERE message LIKE '%Falling back%'
   GROUP BY DATE(created_at), channel_id;
   ```

2. **Primary Provider Failures**
   ```sql
   -- Track which providers are failing
   SELECT channel_id, ai_provider, COUNT(*)
   FROM log_entries
   WHERE message LIKE '%triage error%'
   GROUP BY channel_id, ai_provider;
   ```

3. **Message Processing Success Rate**
   ```sql
   SELECT 
     COUNT(*) as total,
     SUM(CASE WHEN send_status = 'sent' THEN 1 ELSE 0 END) as sent,
     SUM(CASE WHEN send_status = 'failed' THEN 1 ELSE 0 END) as failed
   FROM tele_messages;
   ```

### Alerts to Set Up

1. **Alert if any provider fails >5 times in 1 hour**
   - Indicates systemic issue with that provider
   - Consider switching primary provider

2. **Alert if fallback is used >10% of the time**
   - Indicates primary provider is unreliable
   - May need to switch provider or investigate API key issues

3. **Alert if both primary and fallback fail**
   - System is degraded (messages forwarded unprocessed)
   - Immediate investigation required

## Troubleshooting

### Fallback Not Triggering

Check:
1. Is `ai_fallback_provider` set in database?
   ```sql
   SELECT ai_fallback_provider FROM tele_channels WHERE id = 14;
   ```

2. Is the fallback API key in environment?
   ```bash
   echo $GLM_API_KEY   # Should print key, not empty
   ```

3. Is the primary provider actually failing?
   - Check logs: "AI triage error for..." 
   - If no error, primary provider is succeeding

### Fallback Also Failing

If both primary and fallback fail:
1. Check API keys are valid and have credits
2. Check provider status pages (xai.com, zhipuai.com, openai.com)
3. Check network connectivity (proxy/firewall issues)
4. Check rate limits haven't been hit
5. Review error message in logs for specific issue

### Messages Not Being Processed

If messages are forwarded without being processed (raw text):
1. Verify AI is enabled for that channel
2. Verify both primary and fallback providers are configured
3. Check logs for: "AI triage failed and no fallback configured"
4. Run: `python setup_ai_fallbacks.py --dry-run` to verify config

## Future Improvements

1. **Circuit Breaker**: Temporarily disable providers that fail repeatedly
2. **Provider Health Checks**: Periodic validation that providers are responsive
3. **Fallback Chain**: Support multiple fallbacks (primary → fallback1 → fallback2 → fallback3)
4. **Cost Tracking**: Log which providers used to analyze costs
5. **Dynamic Fallback**: Auto-select fallback based on recent success rate

## Reference

- **Documentation**: See `AI_FALLBACK_GUIDE.md`
- **Setup Script**: `python setup_ai_fallbacks.py`
- **Code**: `ai_services.py` (lines 240-350), `main.py` (line 618-635)
- **Git Commit**: `c0f7457` - "Implement AI provider fallback system for resilience"

---

**Status**: ✅ Ready for deployment

**Next Steps**:
1. Push to production
2. Run `setup_ai_fallbacks.py` to configure channels
3. Monitor logs for normal operation
4. Test by temporarily disabling primary provider

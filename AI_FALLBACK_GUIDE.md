# AI Provider Fallback System

## Overview

The AI fallback system ensures that message processing continues even when the primary AI provider becomes unavailable. This solves the "single point of failure" problem identified on Mar 23 when Grok went down and caused all message processing to fail across all channels.

### Architecture

```
Message received
    ↓
Try primary AI provider
    ├─ Success → Use primary result
    ├─ Timeout/Error → Try fallback
    │   ├─ Success → Use fallback result
    │   └─ Timeout/Error → Forward unchanged (with error reason in logs)
    └─ (Never silently discard)
```

## How It Works

### 1. Database Schema

New columns added to `tele_channels` table:

```sql
ALTER TABLE tele_channels ADD COLUMN ai_fallback_provider TEXT;
ALTER TABLE tele_channels ADD COLUMN ai_fallback_model TEXT;
```

### 2. Configuration

Each channel can have:
- **Primary**: `ai_provider` + `ai_model` (e.g., "grok", "grok-4.1-fast")
- **Fallback**: `ai_fallback_provider` + `ai_fallback_model` (e.g., "glm", "glm-4.7-flashx")

### 3. Retry Logic

Both triage and format passes implement fallback:

```
Triage Pass:
  1. Try: provider=grok, model=grok-4.1-fast
  2. If fails (timeout/error) → Try: provider=glm, model=glm-4.7-flashx
  3. If still fails → Forward unchanged (never discard)

Format Pass:
  1. Try: provider=grok, model=grok-4.1-fast
  2. If fails → Try: provider=glm, model=glm-4.7-flashx
  3. If still fails → Use original text (never drop message)
```

## Setup

### Automatic Configuration

Run the setup script to configure sensible defaults:

```bash
python setup_ai_fallbacks.py --dry-run    # Preview changes
python setup_ai_fallbacks.py                # Apply defaults
```

This configures:
- **Grok** → Fallback to GLM
- **GLM** → Fallback to OpenAI
- **OpenAI** → Fallback to GLM
- **Google, DeepSeek, Sonar** → Fallback to OpenAI

### Manual Configuration

Edit database directly:

```sql
UPDATE tele_channels 
SET ai_fallback_provider = 'glm',
    ai_fallback_model = 'glm-4.7-flashx'
WHERE name = 'SPX Options AI' AND ai_provider = 'grok';
```

Or use the CLI:

```bash
python cli.py channel update <channel_id> --fallback-provider glm --fallback-model glm-4.7-flashx
```

## Current Setup (SPX Channel Example)

**Before:**
```
SPX Options AI:
  - Primary: grok / grok-4.1-fast
  - Fallback: (none)
  - Risk: If Grok down → All SPX messages fail
```

**After:**
```
SPX Options AI:
  - Primary: grok / grok-4.1-fast
  - Fallback: glm / glm-4.7-flashx
  - Risk: If Grok AND GLM both down → Messages still forwarded (unprocessed)
```

## Behavior by Provider Combination

### Primary: Grok, Fallback: GLM

1. **Grok available** → Process with Grok (fast, premium quality)
2. **Grok timeout/error, GLM available** → Process with GLM (cost-effective backup)
3. **Both fail** → Forward unprocessed (with detailed error log)

### Primary: GLM, Fallback: OpenAI

1. **GLM available** → Process with GLM
2. **GLM fails, OpenAI available** → Process with OpenAI (reliable fallback)
3. **Both fail** → Forward unprocessed

## Logging

### Success Cases

```
AI triage [SPX Options AI]: forward — levels updated
AI triage [SPX Options AI] (FALLBACK glm): forward — levels updated
```

### Failure Cases

```
WARNING: AI triage error for 'SPX Options AI' [grok]: Connection timeout — attempting fallback
INFO: [SPX Options AI] Falling back to glm for triage (reason: timeout (grok))
AI triage [SPX Options AI] (FALLBACK glm): forward — levels updated
```

### All Providers Fail

```
ERROR: AI triage error for 'SPX Options AI' [grok]: Connection error
WARNING: AI triage fallback error for 'SPX Options AI' [glm]: Rate limit exceeded
WARNING: AI triage failed and no fallback configured for 'SPX Options AI' — forwarding original
```

## API Keys

Fallback providers require their API keys to be configured:

- **Grok** → `X_API_KEY`
- **GLM** → `GLM_API_KEY`
- **OpenAI** → `OPENAI_API_KEY`
- **DeepSeek** → `DEEPSEEK_API_KEY`
- **Google** → `GOOGLE_API_KEY`
- **Sonar** → `SONAR_API_KEY`

If fallback provider's API key is missing, fallback is skipped (logged as warning).

## Future Enhancements

### Circuit Breaker Pattern

Temporarily disable providers that are consistently failing:

```python
if provider_failed_n_times_in_row > 3:
    logger.warning(f"Provider {provider} disabled (circuit open)")
    skip_to_fallback()
```

### Provider Health Checks

Periodic health checks to detect failures early:

```python
async def check_provider_health(provider, model, api_key):
    """Send test request to check if provider is responsive."""
```

### Cost Tracking

Track which providers are used as fallback to analyze patterns:

```python
INSERT INTO ai_provider_usage (channel_id, provider, was_fallback, timestamp)
```

### Fallback Chain

Support multiple fallbacks (tertiary, quaternary):

```python
ai_fallback_provider_1 = "glm"
ai_fallback_provider_2 = "openai"
ai_fallback_provider_3 = "deepseek"
```

## Troubleshooting

### "Falling back" appears in logs but format isn't changing

This is normal. The fallback provider successfully processed the message, but the formatting may be slightly different. Check that both providers are configured with compatible models.

### Fallback never triggers even though primary should be failing

Check:
1. Verify API key for fallback provider is set in environment
2. Verify `ai_fallback_provider` and `ai_fallback_model` are set in database
3. Check logs for actual provider responses (may be succeeding despite slow)
4. Run `python setup_ai_fallbacks.py --dry-run` to verify configuration

### All messages forwarding without processing

Check:
1. Both primary and fallback are down
2. API keys are missing for both providers
3. Database connection is failing (check logs for "triage error")

## Summary

The AI fallback system provides:
- ✅ **Resilience**: System continues working even when primary provider is down
- ✅ **Transparency**: All fallback attempts are logged
- ✅ **Reliability**: Messages never silently discarded
- ✅ **Flexibility**: Each channel can have different fallback strategies
- ✅ **Cost Optimization**: Use premium providers for critical channels, fallback to cost-effective providers

# AI Fallback System - Quick Reference

## The Problem

**Mar 23**: Grok failed → All 12 channels stopped processing messages → "Disaster"

**Root cause**: Single point of failure at AI provider level

## The Solution

Automatic fallback to secondary provider when primary fails.

## Current Setup

| Channel | Primary | Fallback |
|---------|---------|----------|
| SPX Options AI | Grok | GLM |
| Algo Pro | GLM | OpenAI |
| 11 Trading Signals | GLM | OpenAI |

## What Happens When Grok Fails Now

```
Mar 23 (BEFORE):
  Grok down → SPX channel offline → DISASTER

Today (AFTER):
  Grok down → Try GLM → Success → Message processed
  Logs show: "[SPX Options AI] Falling back to glm for triage"
```

## Essential Commands

### Verify Configuration
```bash
cd telegramForward
sqlite3 <<EOF
SELECT id, name, ai_provider, ai_fallback_provider FROM tele_channels;
EOF
```

### Apply Default Configuration
```bash
python setup_ai_fallbacks.py
```

### Check Fallback Usage (in logs)
```bash
doctl apps logs <app-id> | grep "Falling back"
```

### Manual Configuration
```bash
python cli.py channel update 14 --fallback-provider glm --fallback-model glm-4.7-flashx
```

## Monitoring

### Watch for These Warnings
- `"Falling back to..."` → Primary provider failed, fallback triggered
- `"triage failed and no fallback configured"` → System degraded, investigate

### Watch for These Errors
- `"AI triage error..."` → Provider communication issue
- `"Connection timeout"` → Network or provider slowness
- `"Rate limit exceeded"` → Provider quota hit

## Troubleshooting Flowchart

```
Message not processed?
├─ Check logs for errors
│  ├─ "Falling back" message → Normal, fallback worked
│  ├─ "Connection timeout" → Provider slow or down
│  └─ "triage error" → Check API keys and network
├─ Verify fallback configured
│  └─ SELECT ai_fallback_provider FROM tele_channels WHERE id=?;
├─ Verify API keys in environment
│  ├─ echo $GLM_API_KEY
│  ├─ echo $OPENAI_API_KEY
│  └─ echo $X_API_KEY
└─ Check provider status pages
   ├─ https://status.xai.com (Grok)
   ├─ https://zhipuai.com (GLM)
   └─ https://status.openai.com (OpenAI)
```

## Key Features

✅ Automatic retry with fallback provider  
✅ Messages NEVER silently discarded  
✅ Detailed logging of all attempts  
✅ Per-channel configuration  
✅ Independent fallback strategies  
✅ Zero downtime during provider outages  

## What Changed

1. **Database**: New columns `ai_fallback_provider`, `ai_fallback_model`
2. **ai_services.py**: Automatic retry logic in `triage_message()`
3. **main.py**: Loads and passes fallback configuration
4. **setup_ai_fallbacks.py**: Easy default configuration script

## Commit

```
c0f7457 - Implement AI provider fallback system for resilience
```

## Documentation

- **Full Guide**: `AI_FALLBACK_GUIDE.md`
- **Setup Guide**: `SETUP_AI_FALLBACKS.md`
- **This File**: `AI_FALLBACK_QUICK_REFERENCE.md`

---

**TL;DR**: If Grok fails, system automatically uses GLM. If both fail, message still goes through (unprocessed). Never completely down. Ever.

#!/usr/bin/env python3
"""Verify test channel was added correctly."""
import db

channels = db.get_channels(enabled_only=False)
test_ch = next((ch for ch in channels if ch['chat_id'] == '-1003018959772'), None)
if test_ch:
    print('✓ Test channel found:')
    print(f'  ID: {test_ch["id"]}')
    print(f'  Name: {test_ch["name"]}')
    print(f'  Chat ID: {test_ch["chat_id"]}')
    print(f'  AI Enabled: {test_ch.get("ai_enabled")}')
    print(f'  Primary: {test_ch.get("ai_provider")} / {test_ch.get("ai_model")}')
    print(f'  Fallback: {test_ch.get("ai_fallback_provider")} / {test_ch.get("ai_fallback_model")}')
    print()
    print('Configuration:')
    print('  When message arrives:')
    print('    1. Try Grok (grok-4-1-fast-reasoning)')
    print('    2. If fails → Try Google Gemini 2.0 Flash')
    print('    3. If both fail → Forward unchanged')
else:
    print('✗ Test channel not found')

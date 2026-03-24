#!/usr/bin/env python3
"""Check SPX Options AI configuration."""
import db

channels = db.get_channels(enabled_only=False)
spx = next((ch for ch in channels if 'SPX' in ch['name']), None)
test = next((ch for ch in channels if ch['chat_id'] == '-1003018959772'), None)

if spx:
    print('SPX Options AI (source):')
    print(f'  ID: {spx["id"]}')
    print(f'  Name: {spx["name"]}')
    print(f'  AI Enabled: {spx.get("ai_enabled")}')
    print(f'  Primary: {spx.get("ai_provider")} / {spx.get("ai_model")}')
    print(f'  Fallback: {spx.get("ai_fallback_provider")} / {spx.get("ai_fallback_model")}')
    print(f'  Triage Prompt: {"SET" if spx.get("ai_triage_prompt") else "NOT SET"}')
    print(f'  Format Prompt: {"SET" if spx.get("ai_format_prompt") else "NOT SET"}')
    print()
    
    if test:
        print('KyleTestgroup (current):')
        print(f'  ID: {test["id"]}')
        print(f'  AI Enabled: {test.get("ai_enabled")}')
        print(f'  Primary: {test.get("ai_provider")} / {test.get("ai_model")}')
        print(f'  Fallback: {test.get("ai_fallback_provider")} / {test.get("ai_fallback_model")}')
        print()
        
        # Copy prompts from SPX to test
        print('Updating KyleTestgroup to match SPX Options AI...')
        db.update_channel(
            test['id'],
            ai_provider=spx.get('ai_provider'),
            ai_model=spx.get('ai_model'),
            ai_fallback_provider=spx.get('ai_fallback_provider'),
            ai_fallback_model=spx.get('ai_fallback_model'),
            ai_triage_prompt=spx.get('ai_triage_prompt'),
            ai_format_prompt=spx.get('ai_format_prompt'),
        )
        
        # Verify
        updated = db.get_channels(enabled_only=False)
        test_updated = next((ch for ch in updated if ch['id'] == test['id']), None)
        print()
        print('✓ KyleTestgroup updated to match SPX Options AI:')
        print(f'  Primary: {test_updated.get("ai_provider")} / {test_updated.get("ai_model")}')
        print(f'  Fallback: {test_updated.get("ai_fallback_provider")} / {test_updated.get("ai_fallback_model")}')
        print(f'  Triage Prompt: {"SET" if test_updated.get("ai_triage_prompt") else "NOT SET"}')
        print(f'  Format Prompt: {"SET" if test_updated.get("ai_format_prompt") else "NOT SET"}')

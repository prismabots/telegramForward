#!/usr/bin/env python3
"""Verify fallback configuration."""
import db

channels = db.get_channels(enabled_only=False)
print(f'Total channels: {len(channels)}\n')
for ch in channels:
    if ch.get('ai_enabled'):
        prov = ch.get('ai_provider') or '(global)'
        fallback = ch.get('ai_fallback_provider') or '(none)'
        print(f'ID {ch["id"]:2d} | {ch["name"]:30s} | provider={prov:8s} | fallback={fallback:8s}')

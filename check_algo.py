import db

channels = db.get_channels(enabled_only=False)
t2t = [c for c in channels if 'T2T' in c['name']]

if t2t:
    ch = t2t[0]
    print(f"Channel: {ch['name']}")
    print(f"ID: {ch['id']}")
    print(f"Chat ID: {ch['chat_id']}")
    print(f"Webhook: {ch['discord_webhook'][:50]}...")
    print(f"Status: {'enabled' if ch['enabled'] else 'disabled'}")
    print(f"Role mention: {ch.get('discord_role_id') or 'none'}")
    print(f"AI triage: {'enabled' if ch.get('ai_enabled') else 'disabled'}")
else:
    print("T2T Gold Premium channel not found")

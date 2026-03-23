import db
from load_env import load_environment

load_environment()

channels = db.get_channels(False)
ch = [c for c in channels if c['id']==13][0]
print(f"Channel 13: {ch['name']}")
print(f"Webhook: {ch['discord_webhook']}")

#!/usr/bin/env python3
"""Query Grok API to get team information."""
import os
import requests
import json

api_key = os.environ.get("X_API_KEY")
if not api_key:
    # Try to get from database
    import db
    settings = db.get_all_settings()
    api_key = settings.get("ai_api_key")

if not api_key:
    print("ERROR: X_API_KEY not found in environment or database")
    exit(1)

print(f"Using API key: {api_key[:20]}...")
print()

# Query Grok API for account/team info
headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

# Try different endpoints to get team info
endpoints = [
    "https://api.x.ai/v1/account",
    "https://api.x.ai/v1/team",
    "https://api.x.ai/v1/billing",
]

for endpoint in endpoints:
    try:
        print(f"Trying: {endpoint}")
        resp = requests.get(endpoint, headers=headers, timeout=5)
        print(f"  Status: {resp.status_code}")
        if resp.status_code == 200:
            print(f"  Response: {json.dumps(resp.json(), indent=2)}")
        else:
            print(f"  Response: {resp.text[:200]}")
        print()
    except Exception as e:
        print(f"  Error: {e}")
        print()

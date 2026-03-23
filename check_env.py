#!/usr/bin/env python3
"""Check which API keys are configured."""
import os

print('DigitalOcean Environment Variables:')
print()
x_key = os.environ.get('X_API_KEY')
glm_key = os.environ.get('GLM_API_KEY')
openai_key = os.environ.get('OPENAI_API_KEY')
db_url = os.environ.get('BACKUP_DB_ADMIN_URL')

print(f'X_API_KEY (Grok):      {"SET" if x_key else "NOT SET"}')
if x_key:
    print(f'  Value: {x_key[:20]}...')
    
print(f'GLM_API_KEY (Zhipu):   {"SET" if glm_key else "NOT SET"}')
if glm_key:
    print(f'  Value: {glm_key[:20]}...')
    
print(f'OPENAI_API_KEY:        {"SET" if openai_key else "NOT SET"}')
if openai_key:
    print(f'  Value: {openai_key[:20]}...')
    
print(f'BACKUP_DB_ADMIN_URL:   {"SET" if db_url else "NOT SET"}')

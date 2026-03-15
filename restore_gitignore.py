"""
Restore .gitignore to protect session files after deployment.
"""
import os

gitignore_path = ".gitignore"

print("Restoring .gitignore to protect session files...")

# Read current content
with open(gitignore_path, 'r') as f:
    content = f.read()

# Restore session protection
content = content.replace(
    "# Telethon session files - TEMPORARILY DISABLED TO COMMIT SESSION\n"
    "# *.session\n"
    "# *.session-journal\n"
    "# TODO: Re-enable after session is deployed",
    "# Telethon session files\n"
    "*.session\n"
    "*.session-journal"
)

# Write back
with open(gitignore_path, 'w') as f:
    f.write(content)

print("✓ .gitignore restored")
print()
print("Now commit this change:")
print("  git add .gitignore")
print("  git commit -m 'Restore gitignore session protection'")
print("  git push origin main")

"""
Quick fix for App Platform session regeneration.

This script will:
1. Guide you through creating a new session locally
2. Help you commit and push it to trigger App Platform redeploy
"""
import os
import sys
import subprocess

print("=" * 70)
print("App Platform Session Fix - Quick Guide")
print("=" * 70)
print()

# Check if session exists locally
session_file = "anon.session"
if os.path.exists(session_file):
    print(f"⚠️  Existing session file found: {session_file}")
    response = input("Delete it and create fresh? [y/N]: ").strip().lower()
    if response == 'y':
        os.remove(session_file)
        print("✓ Deleted old session")
    else:
        print("Keeping existing session")
        print()
else:
    print("No existing session file found")
    print()

print("=" * 70)
print("Step 1: Create New Session")
print("=" * 70)
print()
print("Running regenerate_session.py...")
print("You'll be prompted for:")
print("  1. Phone number (with country code, e.g., +1234567890)")
print("  2. Telegram verification code")
print()
input("Press Enter to continue...")

# Run regenerate script
try:
    subprocess.run([sys.executable, "regenerate_session.py"], check=True)
except subprocess.CalledProcessError:
    print("\n❌ Session generation failed!")
    print("Please run manually: python regenerate_session.py")
    sys.exit(1)

print()
print("=" * 70)
print("Step 2: Deploy to App Platform")
print("=" * 70)
print()

if not os.path.exists(session_file):
    print(f"❌ Session file not created: {session_file}")
    print("Please run: python regenerate_session.py")
    sys.exit(1)

print(f"✓ Session file created: {session_file}")
print()
print("Now we'll commit and push it to deploy to App Platform:")
print()
print("Commands to run:")
print()
print("  git add anon.session")
print("  git commit -m 'Add regenerated Telegram session for App Platform'")
print("  git push origin main")
print()

response = input("Run these commands now? [y/N]: ").strip().lower()

if response == 'y':
    try:
        print("\nAdding session file...")
        subprocess.run(["git", "add", session_file], check=True)
        
        print("Committing...")
        subprocess.run([
            "git", "commit", "-m", 
            "Add regenerated Telegram session for App Platform"
        ], check=True)
        
        print("Pushing to GitHub...")
        subprocess.run(["git", "push", "origin", "main"], check=True)
        
        print()
        print("=" * 70)
        print("✓ SUCCESS!")
        print("=" * 70)
        print()
        print("The session has been pushed to GitHub.")
        print("DigitalOcean App Platform will auto-deploy in ~2-5 minutes.")
        print()
        print("⚠️  IMPORTANT: After deployment succeeds:")
        print("   1. Re-enable session gitignore protection")
        print("   2. Run: python restore_gitignore.py")
        print()
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Git command failed: {e}")
        print("You may need to run the commands manually")
        sys.exit(1)
else:
    print("\nSkipped auto-commit. Run manually:")
    print("  git add anon.session")
    print("  git commit -m 'Add regenerated session'")
    print("  git push origin main")

"""
Check current AI model configuration
"""
import db
from load_env import load_environment

load_environment()

settings = db.get_all_settings()

print("\n" + "="*60)
print("CURRENT AI CONFIGURATION")
print("="*60)

provider = settings.get('ai_provider', 'Not set')
model = settings.get('ai_model', 'Not set')

print(f"\nProvider: {provider}")
print(f"Model:    {model}")
print("\n" + "="*60)

print("\n📊 AVAILABLE MODELS:\n")
print("OpenAI Models:")
print("  • gpt-4o-mini      - Fast, cheap, good for most tasks")
print("  • gpt-4o           - More capable, better reasoning")
print("  • gpt-4-turbo      - Previous generation, still strong")
print("\nCost Comparison (per 1M tokens):")
print("  • gpt-4o-mini:     $0.15 input / $0.60 output")
print("  • gpt-4o:          $2.50 input / $10.00 output")
print("  • gpt-4-turbo:     $10.00 input / $30.00 output")
print("\n" + "="*60)

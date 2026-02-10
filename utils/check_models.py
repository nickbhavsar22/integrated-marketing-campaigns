import os
import google.generativeai as genai
from dotenv import load_dotenv, find_dotenv

# Load env safely
load_dotenv(find_dotenv(), override=True)

api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")

if not api_key:
    print("Error: No API Key found in .env")
    exit(1)

print(f"API key: {'configured' if api_key else 'MISSING'}")

genai.configure(api_key=api_key)

print("\nListing available models...")
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"- {m.name}")
except Exception as e:
    print(f"Error listing models: {e}")

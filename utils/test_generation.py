import os
import time
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv, find_dotenv

# Load env
load_dotenv(find_dotenv(), override=True)

api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
if not api_key:
    print("No API Key found.")
    exit(1)

# List of candidates to try, prioritized by likely availability
candidates = [
    "gemini-2.0-flash-lite",      # Often lighter/cheaper
    "gemini-2.0-flash-lite-001",
    "gemini-1.5-flash",           # Standard workhorse
    "gemini-1.5-flash-latest",
    "gemini-flash-latest",        # Alias
    "gemini-pro"                  # Old reliable v1.0
]

print(f"API key: {'configured' if api_key else 'MISSING'}")

for model in candidates:
    print(f"\n--- Testing {model} ---")
    try:
        llm = ChatGoogleGenerativeAI(
            model=model,
            google_api_key=api_key,
            max_retries=0 # Fail fast for this test
        )
        response = llm.invoke("Say 'Hello' if you can hear me.")
        print(f"SUCCESS! {model} responded: {response.content}")
        # If we find one, maybe we should stop? Or check all?
        # Let's stop at the first success to give the user a quick fix.
        print(f"\n>>> RECOMMENDED MODEL: {model} <<<")
        break
    except Exception as e:
        print(f"FAILED {model}: {e}")
        time.sleep(1) # Brief pause

import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

def raw_ping():
    api_key = os.getenv("GEMINI_API_KEY")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent?key={api_key}"
    
    payload = {
        "contents": [{"parts": [{"text": "Reply with exactly one word: Connected."}]}]
    }

    print("📡 Sending raw REST request to Google API (30s timeout)...")
    start_time = time.time()
    
    try:
        # Increased timeout to 30 seconds to survive the server queue
        response = requests.post(url, json=payload, timeout=30)
        elapsed = time.time() - start_time
        
        print(f"\n--- RAW API RESPONSE ({elapsed:.2f} seconds) ---")
        print(f"Status Code: {response.status_code}")
        print(f"Payload: {response.text}")
        print("------------------------\n")
        
    except requests.exceptions.Timeout:
        elapsed = time.time() - start_time
        print(f"❌ FAILED: The request timed out after {elapsed:.2f} seconds.")
    except Exception as e:
        print(f"❌ FAILED: {e}")

if __name__ == "__main__":
    raw_ping()
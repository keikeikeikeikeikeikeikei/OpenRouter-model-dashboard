import requests
import json
import sys

def check_auto_router():
    model_id = "openrouter/auto"
    print(f"Checking details for {model_id}...")
    try:
        resp = requests.get(f"https://openrouter.ai/api/v1/models/{model_id}")
        resp.raise_for_status()
        data = resp.json()
        print(json.dumps(data, indent=2))
        
        # Also check endpoints for auto router just in case
        print(f"\nChecking endpoints for {model_id}...")
        resp_ep = requests.get(f"https://openrouter.ai/api/v1/models/{model_id}/endpoints")
        resp_ep.raise_for_status()
        print(json.dumps(resp_ep.json(), indent=2))
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_auto_router()


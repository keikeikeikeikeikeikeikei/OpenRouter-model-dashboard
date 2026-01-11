import requests
import json
import os

def check_api_structure():
    # 1. Fetch main models list (limit to 1 item to see structure)
    print("Checking /api/v1/models structure...")
    try:
        resp = requests.get("https://openrouter.ai/api/v1/models")
        resp.raise_for_status()
        data = resp.json()
        models = data.get('data', [])
        
        if models:
            # Pick a popular model likely to have multiple providers
            target_model = next((m for m in models if "llama-3" in m['id']), models[0])
            print(f"\nStructure for model: {target_model['id']}")
            print(json.dumps(target_model, indent=2))
        else:
            print("No models found.")
            
    except Exception as e:
        print(f"Error fetching models: {e}")

    # 2. Check endpoints for that model
    if models:
        model_id = target_model['id']
        print(f"\nChecking /api/v1/models/{model_id}/endpoints structure...")
        try:
            resp = requests.get(f"https://openrouter.ai/api/v1/models/{model_id}/endpoints")
            resp.raise_for_status()
            endpoints_data = resp.json()
            print(json.dumps(endpoints_data, indent=2))
        except Exception as e:
            print(f"Error fetching endpoints: {e}")

if __name__ == "__main__":
    check_api_structure()

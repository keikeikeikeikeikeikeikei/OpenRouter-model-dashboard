import json
import os
import pathlib

# Paths
BASE_DIR = pathlib.Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
INPUT_FILE = DATA_DIR / "openrouter_data.json"
OUTPUT_FILE = DATA_DIR / "all_model_providers.json"

def save_provider_info():
    if not os.path.exists(INPUT_FILE):
        print(f"❌ Input file not found: {INPUT_FILE}")
        return

    print(f"📖 Reading from {INPUT_FILE}...")
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    extracted_data = []

    # Iterate through all categories in the grouped data
    for category, models in data.items():
        if not isinstance(models, list):
            continue
            
        for model in models:
            # Check if free
            pricing = model.get('pricing', {})
            is_free = False
            try:
                p_prompt = float(pricing.get('prompt', 0))
                p_completion = float(pricing.get('completion', 0))
                if p_prompt == 0 and p_completion == 0:
                    is_free = True
            except (ValueError, TypeError):
                pass

            info = {
                "id": model.get("id"),
                "name": model.get("name"),
                "is_free": is_free,
                "pricing": pricing,
                "top_provider": model.get("top_provider", {}),
                "context_length": model.get("context_length"),
                # Include architecture as it relates to provider capabilities sometimes
                "architecture": model.get("architecture", {})
            }
            extracted_data.append(info)

    print(f"🔍 Extracted provider info for {len(extracted_data)} models.")
    
    # Sort by is_free (true first) then name
    extracted_data.sort(key=lambda x: (not x['is_free'], x['id']))

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(extracted_data, f, indent=2, ensure_ascii=False)

    print(f"💾 Saved provider info to {OUTPUT_FILE}")

if __name__ == "__main__":
    save_provider_info()

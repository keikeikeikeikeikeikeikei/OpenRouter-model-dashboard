#!/usr/bin/env python3
"""
Fetch all OpenRouter model data.
Uses scripts/get_openrouter_data.py to fetch the raw data,
then processes it into a grouped structure for the dashboard.
"""
import json
import pathlib
import sys
import os

# Create a reference to the scripts directory to import the other script
# We assume this script is run from the root of the project or scripts dir
# If run from root via update.sh:
sys.path.append(str(pathlib.Path(__file__).resolve().parent))

try:
    from get_openrouter_data import fetch_openrouter_data
except ImportError:
    # If running directly from scripts/ dir
    sys.path.append(str(pathlib.Path(__file__).resolve().parent))
    from get_openrouter_data import fetch_openrouter_data

# Paths
BASE_DIR = pathlib.Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
# This file is the raw data fetched by get_openrouter_data.py
RAW_DATA_FILE = "openrouter_data.json" 
# This is the processed file we will create
OUTPUT_FILE = DATA_DIR / "openrouter_data.json"

def process_data(raw_file):
    """Process the raw OpenRouter data into grouped categories."""
    if not os.path.exists(raw_file):
        print(f"❌ Raw data file not found: {raw_file}")
        return False

    with open(raw_file, 'r', encoding='utf-8') as f:
        raw_json = json.load(f)
    
    all_models = raw_json.get('data', [])
    
    grouped = {
        "text": [],
        "image": [],
        "video": [],
        "embedding": [],
        "other": []
    }
    
    print(f"📦 Processing {len(all_models)} OpenRouter models...")
    
    for model in all_models:
        # Determine category based on architecture/modality
        arch = model.get('architecture', {})
        modality = arch.get('modality', '')
        
        # OpenRouter Modalities:
        # text->text (Text)
        # text+image->text (Multimodal Text/Vision)
        # text->image (Image Gen)
        # text->video (Video Gen - if any)
        
        if 'embedding' in model['id'].lower() or 'embed' in model['id'].lower() or modality.endswith('->embedding') or modality.endswith('->embeddings'):
             # Note: modality might be text->embedding if that field exists, but robust check is ID for now.
             grouped['embedding'].append(model) 

        elif modality.endswith('->text'):
            # Must come before 'image->' check if I was doing substring search, 
            # but actually let's prioritize explicit output type.
            # If it outputs text, it's Text/LLM (even if input is image).
            grouped['text'].append(model)
            
        elif modality.endswith('->image') or modality.endswith('->text+image'):
            # Image Generation or Editing
            grouped['image'].append(model)
        
        elif modality.endswith('->video') or 'video->' in modality:
            grouped['video'].append(model)
            
        else:
            # Fallback
            if 'gpt' in model['id'] or 'claude' in model['id'] or 'llama' in model['id']:
                grouped['text'].append(model)
            else:
                grouped['other'].append(model)

    # Save processed data
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(grouped, f, indent=2, ensure_ascii=False)
        
    print(f"💾 Saved processed data to {OUTPUT_FILE}")
    print(f"  - Text: {len(grouped['text'])}")
    print(f"  - Image: {len(grouped['image'])}")
    print(f"  - Video: {len(grouped['video'])}")
    print(f"  - Embedding: {len(grouped['embedding'])}")
    print(f"  - Other: {len(grouped['other'])}")
    
    return True

def main():
    # 1. Fetch Data using the existing script
    # We want to save it to a temporary location or the default location of that script
    # get_openrouter_data saves to `openrouter_data.json` by default in CWD
    
    # We'll run it and let it save to the current working directory's root or wherever
    # Ideally we pass absolute path if possible, but the script takes filename.
    
    # Let's just use the filename 'openrouter_raw_temp.json'
    raw_filename = "openrouter_raw_temp.json"
    
    print("🚀 Fetching data from OpenRouter...")
    success = fetch_openrouter_data(raw_filename)
    
    if not success:
        print("❌ Failed to fetch data from OpenRouter.")
        return

    # 2. Process and Group
    if process_data(raw_filename):
        print("✅ Data update complete.")
        
    # Cleanup temp file
    if os.path.exists(raw_filename):
        os.remove(raw_filename)

if __name__ == "__main__":
    main()

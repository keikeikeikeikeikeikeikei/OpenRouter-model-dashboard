import json
import os
import pathlib

# Paths
BASE_DIR = pathlib.Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
PROVIDERS_FILE = DATA_DIR / "openrouter_data.json" # Source of truth for models
STATS_FILE = DATA_DIR / "openrouterstats_full_scraped.json"
OUTPUT_FILE = DATA_DIR / "all_model_providers_with_stats.json"

def merge_stats():
    if not os.path.exists(PROVIDERS_FILE) or not os.path.exists(STATS_FILE):
        print("❌ Missing input files.")
        return

    print("📖 Merging data into 'all_model_providers_with_stats.json'...")
    with open(PROVIDERS_FILE, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)
    
    with open(STATS_FILE, 'r', encoding='utf-8') as f:
        scraped_stats = json.load(f)

    # Index stats
    stats_map = {}
    for item in scraped_stats:
        raw_name = item.get("model_name", "").strip()
        if raw_name not in stats_map:
            stats_map[raw_name] = []
        stats_map[raw_name].append(item)

    # Flatten categories from openrouter_data.json
    all_models = []
    for cat in raw_data.values():
        if isinstance(cat, list):
            all_models.extend(cat)

    merged_data = []
    for m in all_models:
        mid = m.get("id")
        stat_list = stats_map.get(mid)
        
        if stat_list:
            # Sort by throughput
            def parse_tps(x):
                try: return float(x.get("p50_throughput", "0").replace("tok/s", "").strip())
                except: return 0
            stat_list.sort(key=parse_tps, reverse=True)
            m["throughput_stats"] = stat_list
        else:
            m["throughput_stats"] = []
        
        merged_data.append(m)

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(merged_data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Created {OUTPUT_FILE} with {len(merged_data)} models.")

if __name__ == "__main__":
    merge_stats()
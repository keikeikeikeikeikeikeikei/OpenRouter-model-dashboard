import requests
import json
import sys
import os

# Configuration
API_KEY = os.environ.get("OPENROUTER_API_KEY")
API_URL = "https://openrouter.ai/api/v1/models"
DEFAULT_OUTPUT_FILENAME = "openrouter_data.json"

def fetch_openrouter_data(output_filename=DEFAULT_OUTPUT_FILENAME):
    """
    Fetches model data from OpenRouter API and saves it as JSON.
    
    Args:
        output_filename (str): Name of the file to save the data to
        
    Returns:
        bool: True if successful, False otherwise
    """
    headers = {}
    if API_KEY:
        headers["Authorization"] = f"Bearer {API_KEY}"
    
    urls = [
        "https://openrouter.ai/api/v1/models",
        "https://openrouter.ai/api/v1/embeddings/models"
    ]
    
    all_models = {}
    
    try:
        for url in urls:
            print(f"Querying OpenRouter API: {url}")
            response = requests.get(url, headers=headers)
            
            # Embeddings endpoint might 404 if not available to public yet or something, so handle gracefully
            if response.status_code == 404 and "embeddings" in url:
                 print(f"⚠️  Embeddings endpoint not found or not accessible: {url}")
                 continue
                 
            response.raise_for_status()
            data = response.json()
            
            # Merge into dict by ID to deduplicate
            models_list = data.get('data', [])
            for m in models_list:
                all_models[m['id']] = m
                
        # Convert back to list format expected by downstream scripts
        combined_data = {"data": list(all_models.values())}
        
        with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump(combined_data, f, indent=4, ensure_ascii=False)
        
        print(f"OpenRouter data saved to '{output_filename}'. Total models: {len(all_models)}")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"Error: Failed to query OpenRouter API: {e}", file=sys.stderr)
        return False
    except IOError as e:
        print(f"Error: Could not write to file '{output_filename}': {e}", file=sys.stderr)
        return False

def main():
    """Main function to run the script."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Fetch OpenRouter model data')
    parser.add_argument('-o', '--output', default=DEFAULT_OUTPUT_FILENAME,
                        help=f'Output filename (default: {DEFAULT_OUTPUT_FILENAME})')
    args = parser.parse_args()
    
    success = fetch_openrouter_data(args.output)
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()
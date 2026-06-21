import json
import os

def extract_urls(json_path, output_file='urls.txt'):
    """Reads the master JSON map and saves all 'file' URLs to a text file."""
    if not os.path.exists(json_path):
        print(f"Error: File '{json_path}' not found.")
        return

    with open(json_path, 'r') as f:
        data = json.load(f)
    
    # Path to the drug event partitions
    try:
        partitions = data['results']['drug']['event']['partitions']
        urls = [part['file'] for part in partitions if 'file' in part]
        
        with open(output_file, 'w') as f:
            for url in urls:
                f.write(f"{url}\n")
        
        print(f"Success! {len(urls)} URLs extracted to {output_file}")
        
    except KeyError as e:
        print(f"Error: Could not find the expected data path in the JSON. Missing key: {e}")

if __name__ == "__main__":
    path = input("Enter the path to your master_map.json: ").strip()
    extract_urls(path)
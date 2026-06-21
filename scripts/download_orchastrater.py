import json
import os
import requests
import concurrent.futures

def get_urls_from_json(json_path):
    """Extracts the list of URLs from your JSON master map."""
    with open(json_path, 'r') as f:
        data = json.load(f)
    
    # Path to the drug event partitions
    partitions = data['results']['drug']['event']['partitions']
    urls = [part['file'] for part in partitions if 'file' in part]
    return urls

def save_urls_to_file(urls, output_file):
    """Saves the URLs to a text file (perfect for aria2)."""
    with open(output_file, 'w') as f:
        for url in urls:
            f.write(f"{url}\n")
    print(f"Successfully saved {len(urls)} URLs to {output_file}")

def download_single_file(url, download_dir):
    """Downloads a single file."""
    filename = url.split('/')[-1]
    filepath = os.path.join(download_dir, filename)
    
    if os.path.exists(filepath):
        return f"Skipped: {filename}"
        
    response = requests.get(url, stream=True)
    with open(filepath, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    return f"Downloaded: {filename}"

def main():
    # --- PROMPTS ---
    json_path = input("Enter the full path to your master_map.json file: ").strip()
    target_dir = input("Enter the directory path where you want files/urls.txt saved: ").strip()
    
    # Validate paths
    if not os.path.exists(json_path):
        print(f"Error: The input file '{json_path}' was not found.")
        return
    
    # Create target directory if it doesn't exist
    os.makedirs(target_dir, exist_ok=True)
    
    # 1. Extract
    urls = get_urls_from_json(json_path)
    print(f"Found {len(urls)} links.")
    
    # 2. Save for aria2 (inside the target directory)
    urls_txt_path = os.path.join(target_dir, 'urls.txt')
    save_urls_to_file(urls, urls_txt_path)
    
    # 3. Download
    print(f"Starting parallel download into '{target_dir}'...")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        # Pass target_dir to the downloader
        results = list(executor.map(lambda url: download_single_file(url, target_dir), urls))
        for res in results:
            print(res)

if __name__ == "__main__":
    main()
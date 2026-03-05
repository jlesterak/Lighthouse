#!/usr/bin/env python3
"""
Lighthouse Updater Tool
Designed to download massive offline knowledge repositories (ZIMs) over
unstable, spotty internet connections. Uses only Python standard libraries
to ensure cross-platform compatibility (Windows, Linux, macOS, Android/Termux).
"""

import os
import sys
import json
import urllib.request
import urllib.error
import time

MANIFEST_FILE = "manifest.json"
CONTENT_DIR = "content"

def load_manifest():
    if not os.path.exists(MANIFEST_FILE):
        print(f"Error: {MANIFEST_FILE} not found.", file=sys.stderr)
        sys.exit(1)
    with open(MANIFEST_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def format_bytes(size):
    # 2**10 = 1024
    power = 2**10
    n = 0
    power_labels = {0 : '', 1: 'K', 2: 'M', 3: 'G', 4: 'T'}
    while size > power:
        size /= power
        n += 1
    return f"{size:.2f} {power_labels[n]}B"

def download_file(url, target_path):
    """
    Downloads a file with HTTP Range support for resuming.
    """
    temp_path = target_path + ".part"
    
    # Check if a partial download already exists
    local_size = 0
    if os.path.exists(temp_path):
        local_size = os.path.getsize(temp_path)

    try:
        req = urllib.request.Request(url, method="HEAD")
        with urllib.request.urlopen(req) as resp:
            total_size_str = resp.headers.get("Content-Length")
            supports_ranges = resp.headers.get("Accept-Ranges") == "bytes"
            
            if total_size_str:
                total_size = int(total_size_str)
            else:
                total_size = None
                
    except urllib.error.URLError as e:
        print(f"\nError connecting to server for {url}: {e}")
        return False

    if local_size > 0:
        if total_size and local_size == total_size:
            print("Download already complete (found in .part file). Moving to final destination.")
            os.rename(temp_path, target_path)
            return True
        elif total_size and local_size > total_size:
            print("Local file is larger than remote file. Corrupted? Deleting and starting over.")
            os.remove(temp_path)
            local_size = 0
        elif supports_ranges:
            print(f"Resuming download from byte {local_size}...")
        else:
            print("Server does not support resuming. Starting from scratch.")
            local_size = 0
            if os.path.exists(temp_path):
                os.remove(temp_path)

    # Build the actual request
    req = urllib.request.Request(url)
    if local_size > 0 and supports_ranges:
        req.add_header("Range", f"bytes={local_size}-")

    print(f"Starting download to {temp_path}")
    print("Press Ctrl+C to safely pause/abort the download.")

    mode = "ab" if local_size > 0 and supports_ranges else "wb"
    
    try:
        with urllib.request.urlopen(req, timeout=30) as resp, open(temp_path, mode) as out_file:
            start_time = time.time()
            bytes_downloaded_session = 0
            
            while True:
                chunk = resp.read(8192 * 4) # 32KB chunks
                if not chunk:
                    break
                    
                out_file.write(chunk)
                bytes_downloaded_session += len(chunk)
                current_total = local_size + bytes_downloaded_session
                
                # Simple progress bar
                elapsed = time.time() - start_time
                speed = bytes_downloaded_session / elapsed if elapsed > 0 else 0
                
                if total_size:
                    percent = (current_total / total_size) * 100
                    sys.stdout.write(f"\rProgress: [{percent:.1f}%] {format_bytes(current_total)} / {format_bytes(total_size)} | Speed: {format_bytes(speed)}/s")
                else:
                    sys.stdout.write(f"\rDownloaded: {format_bytes(current_total)} | Speed: {format_bytes(speed)}/s")
                sys.stdout.flush()
                
    except KeyboardInterrupt:
        print("\n\nDownload paused by user. Run the script again to resume.")
        return False
    except urllib.error.URLError as e:
        print(f"\n\nNetwork error: {e}")
        print("Download interrupted. Run the script again later to resume.")
        return False
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        return False

    print("\nDownload finished successfully.")
    
    # If a previous fully downloaded file exists, remove it
    if os.path.exists(target_path):
        os.remove(target_path)
        
    os.rename(temp_path, target_path)
    return True

def print_menu(manifest):
    print("="*60)
    print(" Lighthouse Offline Knowledge Updater")
    print("="*60)
    print(f"Content will be saved to: {os.path.abspath(CONTENT_DIR)}/\n")
    
    item_counter = 1
    item_map = {}
    
    for category in manifest['categories']:
        print(f"--- {category['name']} ---")
        print(f"    {category['description']}")
        
        for item in category['items']:
            print(f"  [{item_counter}] {item['name']} (~{item['size_approx']})")
            print(f"      {item['description']}")
            
            # Check if it already exists
            final_path = os.path.join(CONTENT_DIR, item['filename'])
            if os.path.exists(final_path):
                print("      [STATUS: ALREADY DOWNLOADED]")
            elif os.path.exists(final_path + ".part"):
                print("      [STATUS: PARTIAL DOWNLOAD EXISTS]")
                
            item_map[item_counter] = item
            item_counter += 1
            print()
            
    print("[q] Quit")
    return item_map

def main():
    if not os.path.exists(CONTENT_DIR):
        os.makedirs(CONTENT_DIR)

    manifest = load_manifest()
    
    while True:
        item_map = print_menu(manifest)
        
        choice = input("\nEnter the number of the item to download (or 'q' to quit): ").strip().lower()
        
        if choice == 'q':
            break
            
        try:
            choice_num = int(choice)
            if choice_num not in item_map:
                print("Invalid selection.")
                continue
                
            selected = item_map[choice_num]
            target_path = os.path.join(CONTENT_DIR, selected['filename'])
            
            if os.path.exists(target_path):
                print(f"{selected['name']} is already completely downloaded.")
                redownload = input("Do you want to re-download it? (y/N): ").strip().lower()
                if redownload != 'y':
                    continue
            
            print(f"\nPreparing to download {selected['name']}...")
            download_file(selected['url'], target_path)
            
            input("\nPress Enter to return to the menu...")
            
        except ValueError:
            print("Please enter a valid number.")

if __name__ == "__main__":
    main()

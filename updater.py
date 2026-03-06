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
import urllib.parse
import urllib.error
import xml.etree.ElementTree as ET
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

def search_kiwix_library(query):
    print(f"\nSearching Kiwix library for '{query}'...")
    encoded_query = urllib.parse.quote(query)
    url = f"https://library.kiwix.org/catalog/v2/entries?q={encoded_query}&count=20"
    
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=15) as resp:
            xml_data = resp.read()
    except Exception as e:
        print(f"Error querying Kiwix API: {e}")
        return []
        
    try:
        root = ET.fromstring(xml_data)
    except ET.ParseError as e:
        print(f"Error parsing API response: {e}")
        return []
        
    ns = {'atom': 'http://www.w3.org/2005/Atom'}
    results = []
    
    for entry in root.findall('atom:entry', ns):
        title_node = entry.find('atom:title', ns)
        summary_node = entry.find('atom:summary', ns)
        
        title = title_node.text if title_node is not None else "Unknown Title"
        summary = summary_node.text if summary_node is not None else ""
        
        download_url = None
        size_approx = "Unknown size"
        
        for link in entry.findall('atom:link', ns):
            rel = link.get('rel')
            href = link.get('href')
            if rel == 'http://opds-spec.org/acquisition/open-access' and href:
                if href.endswith('.meta4'):
                    download_url = href[:-6]
                else:
                    download_url = href
                    
                length = link.get('length')
                if length and length.isdigit():
                    size_approx = format_bytes(int(length))
                break
                
        if download_url:
            filename = download_url.split('/')[-1]
            if '?' in filename:
                filename = filename.split('?')[0]
                
            results.append({
                'name': title,
                'description': summary,
                'url': download_url,
                'size_approx': size_approx,
                'filename': filename
            })
            
    return results

def get_exact_zim(query):
    """
    Downloads the full Kiwix catalog XML and searches it locally.
    This guarantees 100% precision for matching exact names and flavours,
    since the Kiwix search API ignores exact string tokens.
    """
    url = "https://library.kiwix.org/catalog/v2/entries"
    
    parts = query.rsplit('_', 1)
    
    if len(parts) == 2:
        flavor_test = parts[1]
        if flavor_test in ['maxi', 'mini', 'nopic', 'novid']:
            target_name = parts[0]
            target_flavor = flavor_test
        else:
            target_name = query
            target_flavor = "None"
    else:
        target_name = query
        target_flavor = "None"

    print(f"\nDownloading Kiwix primary catalog for exact matching...")
    url = "https://library.kiwix.org/catalog/root.xml"
    ns = {'atom': 'http://www.w3.org/2005/Atom'}

    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=30) as resp:
            xml_data = resp.read()
        root = ET.fromstring(xml_data)
    except Exception as e:
        print(f"\nError fetching or parsing catalog search: {e}")
        return None, None

    for entry in root.findall('atom:entry', ns):
        name_node = entry.find('atom:name', ns)
        flavour_node = entry.find('atom:flavour', ns)
        
        entry_name = name_node.text if name_node is not None else "None"
        entry_flavour = flavour_node.text if flavour_node is not None else "None"
        
        if entry_name == target_name:
            if target_flavor != "None" and entry_flavour != target_flavor:
                continue
                
            for link in entry.findall('atom:link', ns):
                if link.get('rel') == 'http://opds-spec.org/acquisition/open-access':
                    href = link.get('href', '')
                    if href.endswith('.meta4'):
                        download_url = href[:-6]
                        filename = download_url.split('/')[-1]
                        if '?' in filename:
                            filename = filename.split('?')[0]
                        return download_url, filename
                        
    print("\n  Search returned results, but no exact name/flavor match found.")
    return None, None

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
            
            # Note: We can no longer stat the file here accurately because the filename
            # is dynamic based on the latest version. User will be notified when they attempt download.
                
            item_map[item_counter] = item
            item_counter += 1
            print()
            
    print("[s] Search entire Kiwix library")
    print("[q] Quit")
    return item_map

def main():
    if not os.path.exists(CONTENT_DIR):
        os.makedirs(CONTENT_DIR)

    manifest = load_manifest()
    
    while True:
        item_map = print_menu(manifest)
        
        choice = input("\nEnter the number(s) to download (comma-separated), 'all', 's' to search, or 'q' to quit: ").strip().lower()
        
        if choice == 'q':
            break
            
        selected_items = []
        if choice == 'all':
            selected_items = list(item_map.values())
        elif choice == 's':
            query = input("Enter search query (e.g., 'medical', 'ubuntu', 'survival'): ").strip()
            if not query:
                continue
            
            results = search_kiwix_library(query)
            if not results:
                print("No results found or error occurred.")
                input("\nPress Enter to return to the menu...")
                continue
                
            print("\n--- Search Results ---")
            search_map = {}
            for i, res in enumerate(results, 1):
                print(f"  [{i}] {res['name']} (~{res['size_approx']})")
                print(f"      {res['description']}")
                # Check if it already exists
                final_path = os.path.join(CONTENT_DIR, res['filename'])
                if os.path.exists(final_path):
                    print("      [STATUS: ALREADY DOWNLOADED]")
                elif os.path.exists(final_path + ".part"):
                    print("      [STATUS: PARTIAL DOWNLOAD EXISTS]")
                print()
                search_map[i] = res
            
            print("  [b] Back to main menu")
            
            sub_choice = input("\nEnter the number(s) to download (comma-separated), 'all', or 'b' to go back: ").strip().lower()
            if sub_choice == 'b':
                continue
                
            if sub_choice == 'all':
                selected_items = list(search_map.values())
            else:
                parts = [p.strip() for p in sub_choice.split(',') if p.strip()]
                invalid = False
                for p in parts:
                    try:
                        sub_choice_num = int(p)
                        if sub_choice_num not in search_map:
                            print(f"Invalid selection: {sub_choice_num}")
                            invalid = True
                            break
                        selected_items.append(search_map[sub_choice_num])
                    except ValueError:
                        print("Please enter valid numbers.")
                        invalid = True
                        break
                if invalid or not selected_items:
                    continue
        else:
            parts = [p.strip() for p in choice.split(',') if p.strip()]
            invalid = False
            for p in parts:
                try:
                    choice_num = int(p)
                    if choice_num not in item_map:
                        print(f"Invalid selection: {choice_num}")
                        invalid = True
                        break
                    selected_items.append(item_map[choice_num])
                except ValueError:
                    print("Please enter valid numbers, 'all', or 's' to search.")
                    invalid = True
                    break
            if invalid or not selected_items:
                continue
            
        for selected in selected_items:
            if 'catalog_query' in selected:
                print(f"\nResolving latest version of {selected['name']} via Kiwix catalog...")
                url_to_download, filename = get_exact_zim(selected['catalog_query'])
                
                if not url_to_download:
                    print(f"Failed to find {selected['name']} in the Kiwix catalog. Skipping.")
                    continue
                    
                target_path = os.path.join(CONTENT_DIR, filename)
            else:
                url_to_download = selected['url']
                target_path = os.path.join(CONTENT_DIR, selected['filename'])
            
            if os.path.exists(target_path):
                print(f"{selected['name']} ({os.path.basename(target_path)}) is already completely downloaded.")
                redownload = input(f"Do you want to re-download {selected['name']}? (y/N): ").strip().lower()
                if redownload != 'y':
                    continue
            
            print(f"\nPreparing to download {selected['name']}...")
            success = download_file(url_to_download, target_path)
            if not success:
                print(f"Download aborted or failed for {selected['name']}. Stopping batch.")
                break
        
        input("\nPress Enter to return to the menu...")

if __name__ == "__main__":
    main()

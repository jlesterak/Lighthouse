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
import hashlib
import re

# Resolve paths next to this script so it works from any working directory,
# including when run straight off the USB stick.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MANIFEST_FILE = os.path.join(BASE_DIR, "manifest.json")
VERSION_FILE = os.path.join(BASE_DIR, "VERSION")
CONTENT_DIR = os.path.join(BASE_DIR, "content")

CATALOG_URL = "https://library.kiwix.org/catalog/v2/entries"
ACQUISITION_REL = "http://opds-spec.org/acquisition/open-access"
OPDS_NS = {'atom': 'http://www.w3.org/2005/Atom'}

# How hard to keep trying before giving up on a flaky connection
MAX_RETRIES = 10
MAX_BACKOFF = 60
CHUNK_SIZE = 8192 * 4  # 32KB chunks


def get_version():
    """The project version, from the VERSION file (the single source of truth)."""
    try:
        with open(VERSION_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    except OSError:
        return "unknown"

def _install_user_agent():
    """Every request identifies itself. Wikimedia's servers (dumps.wikimedia.org, where Kiwix's
    load balancer sends some files) refuse Python's default "Python-urllib/3.x" user agent with
    403, which used to stall the whole download queue on those files."""
    opener = urllib.request.build_opener()
    opener.addheaders = [("User-Agent", f"Lighthouse-updater/{get_version()} (+https://github.com/jlesterak/Lighthouse)")]
    urllib.request.install_opener(opener)


_install_user_agent()


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
    while size > power and n < 4:
        size /= power
        n += 1
    return f"{size:.2f} {power_labels[n]}B"

def get_remote_size(url):
    """
    The file's size in bytes, or None if the server won't say.

    Asks with HEAD first. Some Kiwix mirrors refuse HEAD (403/405) while serving the file
    normally, so on an HTTP error it asks for the first byte instead and reads the total
    from Content-Range. If that is refused too, returns None: the download still works,
    just without a percentage, and the SHA-256 check still guards the result. Network
    failures (no connection, timeouts) still raise, so the caller retries them.
    """
    try:
        req = urllib.request.Request(url, method="HEAD")
        with urllib.request.urlopen(req, timeout=30) as resp:
            total_size_str = resp.headers.get("Content-Length")
        return int(total_size_str) if total_size_str else None
    except urllib.error.HTTPError:
        pass
    try:
        req = urllib.request.Request(url, headers={"Range": "bytes=0-0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            content_range = resp.headers.get("Content-Range", "")
        match = re.match(r"bytes \d+-\d+/(\d+)", content_range)
        return int(match.group(1)) if match else None
    except urllib.error.HTTPError:
        return None

def _download_attempt(url, temp_path, total_size):
    """
    One pass at fetching the file into temp_path, resuming if possible.
    Returns True when the file is complete. Raises OSError (which includes
    URLError and socket timeouts) on network trouble.
    """
    local_size = os.path.getsize(temp_path) if os.path.exists(temp_path) else 0

    if local_size > 0:
        if total_size and local_size == total_size:
            return True
        if total_size and local_size > total_size:
            print("Local file is larger than remote file. Corrupted? Deleting and starting over.")
            local_size = 0
        else:
            print(f"Resuming download from byte {local_size}...")

    req = urllib.request.Request(url)
    if local_size > 0:
        req.add_header("Range", f"bytes={local_size}-")

    with urllib.request.urlopen(req, timeout=30) as resp:
        if local_size > 0 and resp.status != 206:
            # Server doesn't support resuming and is sending the whole file;
            # appending it would corrupt the download.
            print("Server does not support resuming. Starting from scratch.")
            local_size = 0

        mode = "ab" if local_size > 0 else "wb"
        with open(temp_path, mode) as out_file:
            start_time = time.time()
            bytes_downloaded_session = 0

            while True:
                chunk = resp.read(CHUNK_SIZE)
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

    final_size = os.path.getsize(temp_path)
    if total_size and final_size < total_size:
        # The connection closed cleanly but early; treat it as an interruption
        raise ConnectionError(f"connection closed at {final_size} of {total_size} bytes")
    return True

def download_file(url, target_path, max_retries=MAX_RETRIES, max_backoff=MAX_BACKOFF):
    """
    Downloads a file with HTTP Range support for resuming. Retries network
    failures automatically with exponential backoff, resuming each time.
    """
    temp_path = target_path + ".part"

    print(f"Starting download to {temp_path}")
    print("Press Ctrl+C to safely pause/abort the download.")

    attempt = 0
    while True:
        try:
            total_size = get_remote_size(url)
            if _download_attempt(url, temp_path, total_size):
                break
        except KeyboardInterrupt:
            print("\n\nDownload paused by user. Run the script again to resume.")
            return False
        except OSError as e:
            attempt += 1
            if attempt > max_retries:
                print(f"\n\nNetwork error: {e}")
                print(f"Gave up after {max_retries} retries. Run the script again later to resume.")
                return False
            delay = min(2 ** attempt, max_backoff)
            print(f"\n\nNetwork error: {e}")
            print(f"Retrying in {delay}s (attempt {attempt}/{max_retries})...")
            try:
                time.sleep(delay)
            except KeyboardInterrupt:
                print("\nDownload paused by user. Run the script again to resume.")
                return False

    print("\nDownload finished successfully.")

    expected = fetch_expected_sha256(url)
    if expected is None:
        print("No checksum is published for this file; skipping verification.")
    else:
        print("Verifying SHA-256 checksum (this takes a while for large files)...")
        try:
            actual = sha256_of(temp_path)
        except KeyboardInterrupt:
            print("\nVerification interrupted. Run the script again to finish it.")
            return False
        if actual != expected:
            print("Checksum mismatch: the download is corrupt. Deleting it; run the script again to re-download.")
            os.remove(temp_path)
            return False
        print("Checksum verified.")

    # os.replace overwrites an existing file on every platform, including Windows
    os.replace(temp_path, target_path)
    return True

def fetch_expected_sha256(url):
    """
    Kiwix publishes `<file>.sha256` next to every ZIM. Returns the hex digest,
    or None when there isn't one (or it can't be fetched).
    """
    try:
        with urllib.request.urlopen(url + ".sha256", timeout=30) as resp:
            text = resp.read(4096).decode("ascii", errors="replace")
    except OSError:
        return None
    match = re.match(r"\s*([0-9a-fA-F]{64})\b", text)
    return match.group(1).lower() if match else None

def sha256_of(path):
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()

def parse_opds_entries(xml_data):
    """
    Parses a Kiwix OPDS v2 feed into a list of dicts with the catalog name,
    flavour, title, description, direct download URL, filename and size.
    Entries without a download link are skipped.
    """
    root = ET.fromstring(xml_data)
    results = []

    for entry in root.findall('atom:entry', OPDS_NS):
        def text(tag, default=""):
            node = entry.find(f'atom:{tag}', OPDS_NS)
            return node.text if node is not None and node.text else default

        for link in entry.findall('atom:link', OPDS_NS):
            href = link.get('href')
            if link.get('rel') != ACQUISITION_REL or not href:
                continue

            # The catalog links a Metalink file; the ZIM sits at the same URL minus .meta4
            download_url = href[:-6] if href.endswith('.meta4') else href
            filename = download_url.split('/')[-1].split('?')[0]
            length = link.get('length')

            results.append({
                'catalog_name': text('name'),
                'flavour': text('flavour'),
                'name': text('title', "Unknown Title"),
                'description': text('summary'),
                'url': download_url,
                'filename': filename,
                'size_approx': format_bytes(int(length)) if length and length.isdigit() else "Unknown size",
            })
            break

    return results

def fetch_catalog(params, timeout=30):
    url = f"{CATALOG_URL}?{urllib.parse.urlencode(params)}"
    with urllib.request.urlopen(url, timeout=timeout) as resp:
        return parse_opds_entries(resp.read())

def search_kiwix_library(query):
    print(f"\nSearching Kiwix library for '{query}'...")
    try:
        return fetch_catalog({'q': query, 'count': 20}, timeout=15)
    except (OSError, ET.ParseError) as e:
        print(f"Error querying Kiwix API: {e}")
        return []

def resolve_catalog_item(catalog_name, flavour=""):
    """
    Finds the latest download for an exact catalog name and flavour.
    The catalog's `name` filter is an exact match, unlike the `q` search.
    Returns (download_url, filename), or (None, None) if not found.
    """
    try:
        entries = fetch_catalog({'name': catalog_name, 'count': -1})
    except (OSError, ET.ParseError) as e:
        print(f"\nError fetching the Kiwix catalog: {e}")
        return None, None

    for entry in entries:
        if entry['catalog_name'] == catalog_name and entry['flavour'] == flavour:
            return entry['url'], entry['filename']

    available = ", ".join(sorted(e['flavour'] or "(none)" for e in entries)) or "none"
    print(f"\n  No catalog entry for {catalog_name} with flavour '{flavour or '(none)'}'. Flavours available: {available}")
    return None, None

def print_menu(manifest):
    print("="*60)
    print(f" Lighthouse Offline Knowledge Updater v{get_version()}")
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
            if 'catalog_name' in selected and 'url' not in selected:
                print(f"\nResolving latest version of {selected['name']} via Kiwix catalog...")
                url_to_download, filename = resolve_catalog_item(selected['catalog_name'], selected.get('flavour', ''))
                
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
    if len(sys.argv) > 1 and sys.argv[1] in ("--version", "-V"):
        print(f"Lighthouse {get_version()}")
        sys.exit(0)
    main()

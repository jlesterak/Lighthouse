#!/bin/bash
# Lighthouse Reader Downloader
# Fetches the latest standalone Kiwix readers for Windows, Linux, and Android
# dropping them into the `readers/` directory for the USB build.

set -euo pipefail

cd "$(dirname "$0")"

READERS_DIR="readers"
DOWNLOAD_DIR="$READERS_DIR/.downloads"
VERSIONS_FILE="$READERS_DIR/VERSIONS.txt"

# Kiwix's unversioned permalinks redirect to the latest release
ANDROID_URL="https://download.kiwix.org/release/kiwix-android/kiwix.apk"
LINUX_URL="https://download.kiwix.org/release/kiwix-desktop/kiwix-desktop_x86_64.appimage"
WIN_URL="https://download.kiwix.org/release/kiwix-desktop/kiwix-desktop_windows_x64.zip"

for cmd in curl unzip; do
    if ! command -v "$cmd" &> /dev/null; then
        echo "Error: '$cmd' is required. Install it with: sudo apt install $cmd"
        exit 1
    fi
done

mkdir -p "$DOWNLOAD_DIR"
touch "$VERSIONS_FILE"

# fetch URL -> prints the local path of the versioned download.
# Resolving the redirect first means each release gets its own file, so
# resuming (-C -) never appends a new release onto an older one.
fetch() {
    local url=$1 real_url filename
    real_url=$(curl -fsSIL -o /dev/null -w '%{url_effective}' "$url")
    filename=$(basename "${real_url%%\?*}")
    echo "  Latest release: $filename" >&2
    curl -fL --retry 5 --retry-delay 5 -C - --progress-bar -o "$DOWNLOAD_DIR/$filename" "$real_url" >&2
    echo "$DOWNLOAD_DIR/$filename"
}

# up_to_date NAME FILE -> true if VERSIONS.txt says NAME is already FILE
up_to_date() {
    grep -qxF "$1: $(basename "$2")" "$VERSIONS_FILE"
}

# Hardlink from the download cache when possible so readers don't take twice the space
install_file() {
    rm -f "$2"
    ln "$1" "$2" 2>/dev/null || cp "$1" "$2"
}

record_version() {
    local tmp
    tmp=$(mktemp)
    grep -v "^$1: " "$VERSIONS_FILE" > "$tmp" || true
    echo "$1: $(basename "$2")" >> "$tmp"
    sort "$tmp" > "$VERSIONS_FILE"
    rm -f "$tmp"
}

echo "======================================"
echo " Lighthouse Reader Fetcher"
echo "======================================"
echo "Downloading Kiwix binaries to $READERS_DIR/"

# 1. Android APK
echo "[1/3] Android APK..."
apk=$(fetch "$ANDROID_URL")
if ! up_to_date android "$apk"; then
    install_file "$apk" "$READERS_DIR/kiwix-android.apk"
    record_version android "$apk"
fi

# 2. Linux AppImage
echo "[2/3] Linux AppImage..."
appimage=$(fetch "$LINUX_URL")
if ! up_to_date linux "$appimage"; then
    install_file "$appimage" "$READERS_DIR/kiwix-desktop.AppImage"
    chmod +x "$READERS_DIR/kiwix-desktop.AppImage"
    record_version linux "$appimage"
fi

# 3. Windows Portable (ZIP), extracted so the user just sees an .exe
echo "[3/3] Windows Portable..."
winzip=$(fetch "$WIN_URL")
if ! up_to_date windows "$winzip"; then
    echo "Extracting Windows binaries..."
    extract_dir=$(mktemp -d "$DOWNLOAD_DIR/extract.XXXXXX")
    unzip -q -o "$winzip" -d "$extract_dir"
    # The zip normally holds one top-level folder named after the release
    shopt -s nullglob
    entries=("$extract_dir"/*)
    shopt -u nullglob
    if [ "${#entries[@]}" -eq 1 ] && [ -d "${entries[0]}" ]; then
        src="${entries[0]}"
    else
        src="$extract_dir"
    fi
    rm -rf "$READERS_DIR/windows"
    mv "$src" "$READERS_DIR/windows"
    chmod 755 "$READERS_DIR/windows"  # mktemp -d creates it 0700
    rm -rf "$extract_dir"
    record_version windows "$winzip"
fi

# Drop superseded releases so old versions don't pile up
for f in "$DOWNLOAD_DIR"/*; do
    [ -f "$f" ] || continue
    grep -qF ": $(basename "$f")" "$VERSIONS_FILE" || rm -f "$f"
done

echo "======================================"
echo "All readers are up to date:"
sed 's/^/  /' "$VERSIONS_FILE"
echo "Android: $READERS_DIR/kiwix-android.apk"
echo "Linux:   $READERS_DIR/kiwix-desktop.AppImage"
echo "Windows: $READERS_DIR/windows/kiwix-desktop.exe"

#!/bin/bash
# Lighthouse Reader Downloader
# Fetches the standalone Kiwix readers for Windows, Linux, and Android
# dropping them into the `readers/` directory for the USB build.

set -e

READERS_DIR="readers"
mkdir -p "$READERS_DIR"

echo "======================================"
echo " Lighthouse Reader Fetcher"
echo "======================================"
echo "Downloading Kiwix binaries to $READERS_DIR/"

# 1. Android APK
echo "[1/3] Downloading Android APK..."
ANDROID_URL="https://download.kiwix.org/release/kiwix-android/kiwix-3.9.2.apk"
wget -c -q --show-progress -O "$READERS_DIR/kiwix-android.apk" "$ANDROID_URL"

# 2. Linux AppImage
echo "[2/3] Downloading Linux AppImage..."
LINUX_URL="https://download.kiwix.org/release/kiwix-desktop/kiwix-desktop_x86_64_2.3.1.appimage"
wget -c -q --show-progress -O "$READERS_DIR/kiwix-desktop.AppImage" "$LINUX_URL"
chmod +x "$READERS_DIR/kiwix-desktop.AppImage"

# 3. Windows Portable (ZIP)
# We will download the ZIP and extract it so the user just sees an .exe
echo "[3/3] Downloading Windows Portable..."
WIN_URL="https://download.kiwix.org/release/kiwix-desktop/kiwix-desktop_windows_x64_2.3.1.zip"
wget -c -q --show-progress -O "$READERS_DIR/kiwix-windows.zip" "$WIN_URL"

echo "Extracting Windows binaries..."
unzip -q -o "$READERS_DIR/kiwix-windows.zip" -d "$READERS_DIR/"
# The zip contains a folder called "kiwix-desktop_windows_x64_2.3.1"
# Let's cleanly rename it to "windows"
rm -rf "$READERS_DIR/windows"
mv "$READERS_DIR/kiwix-desktop_windows_x64_2.3.1" "$READERS_DIR/windows"
rm "$READERS_DIR/kiwix-windows.zip"

echo "======================================"
echo "All readers downloaded successfully!"
echo "Android: $READERS_DIR/kiwix-android.apk"
echo "Linux:   $READERS_DIR/kiwix-desktop.AppImage"
echo "Windows: $READERS_DIR/windows/kiwix-desktop.exe"

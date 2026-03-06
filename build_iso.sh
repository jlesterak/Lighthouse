#!/bin/bash
# Lighthouse ISO Builder Script
# Automates the creation of the customized Debian Live OS ISO

set -e

echo "================================================="
echo " Lighthouse Live OS ISO Builder"
echo "================================================="

TARGET_ARCH=${1:-amd64}
echo "Target Architecture: $TARGET_ARCH"
export LB_ARCHITECTURE="$TARGET_ARCH"

if [ "$EUID" -ne 0 ]; then
  echo "Please run this script as root (sudo)."
  exit 1
fi

if ! command -v lb &> /dev/null; then
    echo "Error: 'live-build' is not installed."
    echo "Please install it via: sudo apt update && sudo apt install live-build"
    exit 1
fi

if [ ! -d "LiveOS" ]; then
    echo "Error: LiveOS directory not found. Please run this script from the Lighthouse repository root."
    exit 1
fi

echo "Moving to LiveOS directory..."
cd LiveOS || exit 1

echo "Cleaning previous builds..."
lb clean

echo "Configuring build environment..."
lb config

echo "Building the ISO... "
echo "(This may take 30-60 minutes depending on your internet connection and CPU)"
echo "-------------------------------------------------"
lb build

ISO_FILE="live-image-${TARGET_ARCH}.hybrid.iso"
if [ -f "$ISO_FILE" ]; then
    echo "-------------------------------------------------"
    echo "================================================="
    echo " Build Complete!"
    echo " Your Live OS ISO is located at: LiveOS/$ISO_FILE"
    echo " You can now run build_usb.sh to flash it to a USB drive."
    echo "================================================="
else
    echo "-------------------------------------------------"
    echo "Error: $ISO_FILE was not created. Check the build logs above for errors."
    exit 1
fi

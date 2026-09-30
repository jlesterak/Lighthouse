#!/bin/bash
# Lighthouse ISO Builder Script
# Automates the creation of the customized Debian Live OS ISO

set -e

echo "================================================="
echo " Lighthouse Live OS ISO Builder"
echo "================================================="

TARGET_ARCH=${1:-amd64}
case "$TARGET_ARCH" in
    amd64) QEMU_ARCH=x86_64 ;;
    arm64) QEMU_ARCH=aarch64 ;;
    *)
        echo "Error: unsupported architecture '$TARGET_ARCH'. Use amd64 or arm64."
        exit 1
        ;;
esac
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

# Cross-building runs the target's binaries through qemu-user via binfmt_misc
HOST_ARCH=$(dpkg --print-architecture)
if [ "$TARGET_ARCH" != "$HOST_ARCH" ]; then
    echo "Cross-building $TARGET_ARCH on a $HOST_ARCH host."
    if [ ! -x "/usr/bin/qemu-$QEMU_ARCH-static" ]; then
        echo "Error: /usr/bin/qemu-$QEMU_ARCH-static not found."
        echo "Please install it via: sudo apt install qemu-user-static binfmt-support"
        exit 1
    fi
    if ! grep -qs '^enabled' "/proc/sys/fs/binfmt_misc/qemu-$QEMU_ARCH"; then
        echo "Error: the binfmt handler for $QEMU_ARCH is not registered."
        echo "Try: sudo systemctl restart systemd-binfmt  (or reinstall qemu-user-static)"
        exit 1
    fi
fi

if [ ! -d "LiveOS" ]; then
    echo "Error: LiveOS directory not found. Please run this script from the Lighthouse repository root."
    exit 1
fi

echo "Moving to LiveOS directory..."
cd LiveOS || exit 1

echo "Cleaning previous builds..."
lb clean
# lb config reloads these generated files, so settings from a build for another
# architecture (bootloaders, qemu) would leak into this one. auto/config recreates them.
rm -f config/binary config/bootstrap config/chroot config/common config/source

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

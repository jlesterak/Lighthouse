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

# Ubuntu ships a fork of live-build frozen at 3.0~a57, which can't build a modern
# Debian image (it rejects --bootloaders, among others). Require Debian's.
LB_VERSION=$(lb --version 2>/dev/null | head -n 1)
case "$LB_VERSION" in
    [0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]*) ;;
    *)
        echo "Error: live-build $LB_VERSION is too old; Lighthouse needs Debian's live-build 20230502 or newer."
        echo "Ubuntu and Pop!_OS ship an old fork. Install Debian's package instead:"
        echo "  curl -LO https://deb.debian.org/debian/pool/main/l/live-build/live-build_20230502_all.deb"
        echo "  sudo apt install ./live-build_20230502_all.deb"
        exit 1
        ;;
esac

if ! command -v xorriso &> /dev/null; then
    echo "Error: 'xorriso' is not installed."
    echo "Please install it via: sudo apt install xorriso"
    exit 1
fi

# debootstrap verifies the Debian archive signature; Ubuntu-based hosts lack the key
if [ ! -f /usr/share/keyrings/debian-archive-keyring.gpg ]; then
    echo "Error: the Debian archive keyring is missing, so the bookworm download can't be verified."
    echo "Please install it via: sudo apt install debian-archive-keyring"
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
# lb clean keeps cache/, and the cached bootstrap stage is architecture-specific:
# without this, an arm64 build after an amd64 one silently restores an amd64
# base system. Downloaded .debs are kept; apt ignores other architectures'.
if [ -d cache ] && [ "$(cat cache/.lighthouse-arch 2>/dev/null)" != "$TARGET_ARCH" ]; then
    echo "Cache was built for another architecture; dropping its bootstrap stage..."
    rm -rf cache/bootstrap cache/contents.chroot
fi
mkdir -p cache
echo "$TARGET_ARCH" > cache/.lighthouse-arch
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

# Without syslinux (arm64 is UEFI only), live-build's -isohybrid-gpt-basdat has
# no effect and the ISO gets no partition table at all: written to a stick it
# won't boot on most UEFI firmware, and build_usb.sh can't append the data
# partition. Add an MBR with the EFI image as a real ESP, the way Debian's own
# arm64 ISOs are laid out.
if [ -f "$ISO_FILE" ] && ! sfdisk -d "$ISO_FILE" > /dev/null 2>&1; then
    echo "Adding a partition table with an EFI system partition to the ISO..."
    WORK_DIR=$(mktemp -d)
    xorriso -osirrox on -indev "$ISO_FILE" -extract /boot/grub/efi.img "$WORK_DIR/efi.img"
    xorriso -indev "$ISO_FILE" -outdev "$WORK_DIR/hybrid.iso" \
        -boot_image any replay \
        -append_partition 2 0xef "$WORK_DIR/efi.img" \
        -boot_image any partition_cyl_align=all \
        -changes_pending yes -commit
    mv "$WORK_DIR/hybrid.iso" "$ISO_FILE"
    rm -rf "$WORK_DIR"
    sfdisk -d "$ISO_FILE" > /dev/null
fi

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

#!/bin/bash
# Lighthouse USB Builder Script
# WARNING: This script performs destructive operations on the specified block device.
# It flashes the Live OS ISO and creates an exFAT partition in the remaining space.

set -euo pipefail

cd "$(dirname "$0")"

# Must match LABEL in LiveOS/.../lighthouse-mount.sh (exFAT labels max out at 11 chars)
DATA_LABEL="LIGHTHOUSE"

if [ "$EUID" -ne 0 ]; then
  echo "Please run this script as root (sudo)."
  exit 1
fi

if [ -z "${1:-}" ]; then
  echo "Usage: sudo $0 /dev/sdX [amd64|arm64]"
  echo "Replace /dev/sdX with your USB drive device name."
  echo "Run 'lsblk' to find the correct device. DO NOT guess."
  echo "Architecture defaults to amd64 if not provided."
  exit 1
fi

DEVICE=$1
TARGET_ARCH=${2:-amd64}
ISO_FILE="LiveOS/live-image-${TARGET_ARCH}.hybrid.iso"

for cmd in lsblk sfdisk partprobe mkfs.exfat udevadm; do
  if ! command -v "$cmd" &> /dev/null; then
    echo "Error: '$cmd' not found. Install with: sudo apt install util-linux fdisk parted exfatprogs"
    exit 1
  fi
done

# Check if the device exists and is a whole disk, not a partition
if [ ! -b "$DEVICE" ]; then
  echo "Error: Device $DEVICE not found or is not a physical block device."
  exit 1
fi
if [ "$(lsblk -dno TYPE "$DEVICE")" != "disk" ]; then
  echo "Error: $DEVICE is not a whole disk. Give the disk (e.g. /dev/sdb), not a partition (/dev/sdb1)."
  exit 1
fi

# Never touch a disk holding the running system, whatever its name
SYSTEM_MOUNTS=$(lsblk -nro MOUNTPOINT "$DEVICE" | grep -xE '/|/boot|/boot/efi|/home|/usr|/var|\[SWAP\]' || true)
if [ -n "$SYSTEM_MOUNTS" ]; then
  echo "Error: $DEVICE holds the running system (mounted at: $(echo $SYSTEM_MOUNTS)). Refusing to wipe it."
  exit 1
fi

# Anything that isn't a removable USB device gets an extra, explicit confirmation
REMOVABLE=$(lsblk -dno RM "$DEVICE" | tr -d ' ')
TRANSPORT=$(lsblk -dno TRAN "$DEVICE" | tr -d ' ')
if [ "$REMOVABLE" != "1" ] && [ "$TRANSPORT" != "usb" ]; then
  echo "WARNING: $DEVICE is not a removable USB device (transport: ${TRANSPORT:-unknown})."
  echo "It looks like an internal drive."
  read -r -p "Are you ABSOLUTELY SURE you want to completely wipe $DEVICE? (type 'yes-wipe'): " confirmation
  if [ "$confirmation" != "yes-wipe" ]; then
    echo "Aborting."
    exit 1
  fi
fi

# Verify ISO exists
if [ ! -f "$ISO_FILE" ]; then
  echo "Error: $ISO_FILE not found. Please build the Live OS first."
  echo "sudo ./build_iso.sh $TARGET_ARCH"
  exit 1
fi

# Warn early if the content can't possibly fit
ISO_BYTES=$(stat -c %s "$ISO_FILE")
DISK_BYTES=$(lsblk -dbno SIZE "$DEVICE")
CONTENT_BYTES=$( (du -scb content readers 2>/dev/null || true) | tail -n 1 | cut -f1)
if [ "$(( ISO_BYTES + CONTENT_BYTES ))" -gt "$DISK_BYTES" ]; then
  echo "Error: ISO + content need $(( (ISO_BYTES + CONTENT_BYTES) / 1000000000 )) GB, but $DEVICE is only $(( DISK_BYTES / 1000000000 )) GB."
  exit 1
fi

echo "================================================="
echo " Lighthouse USB Flasher"
echo "================================================="
lsblk -o NAME,SIZE,TYPE,TRAN,MODEL,MOUNTPOINT "$DEVICE"
echo ""
echo "Target Device: $DEVICE"
echo "Target ISO:    $ISO_FILE"
echo ""
echo "WARNING: ALL DATA ON $DEVICE WILL BE DESTROYED."
echo "================================================="
read -r -p "Type the device name ($DEVICE) to continue, or anything else to abort: " confirm_device
if [ "$confirm_device" != "$DEVICE" ]; then
  echo "Aborting."
  exit 1
fi

# 1. Unmount any existing partitions
echo "Unmounting any existing partitions on $DEVICE..."
{ lsblk -nro MOUNTPOINT "$DEVICE" | grep -v '^$' || true; } | while read -r mp; do
  umount "$mp" || true
done

# 2. Flash the Live ISO
echo "Flashing Live ISO to $DEVICE using dd..."
echo "(This may take a few minutes depending on your USB speed)"
dd if="$ISO_FILE" of="$DEVICE" bs=4M status=progress conv=fsync

# 3. Create a new partition in the remaining space
echo "Creating exFAT data partition in the remaining free space..."
partprobe "$DEVICE" || true
udevadm settle

# The hybrid ISO carries its own partitions (the ISO itself, plus the EFI image).
# Append one exFAT (type 7) partition after them and confirm exactly one appeared,
# so a failure can never lead to formatting one of the ISO's partitions.
parts_before=$(sfdisk -d "$DEVICE" | grep -c '^/dev/' || true)
echo ',,7' | sfdisk --append --no-reread "$DEVICE"
parts_after=$(sfdisk -d "$DEVICE" | grep -c '^/dev/' || true)
if [ "$parts_after" -ne "$(( parts_before + 1 ))" ]; then
  echo "Error: expected one new partition (had $parts_before, now $parts_after). Exiting."
  exit 1
fi

partprobe "$DEVICE" || true
udevadm settle

# The new partition is the last entry sfdisk lists
DATA_PART=$(sfdisk -d "$DEVICE" | grep '^/dev/' | tail -n 1 | cut -d' ' -f1)
for _ in $(seq 1 10); do
  [ -b "$DATA_PART" ] && break
  sleep 1
done
if [ ! -b "$DATA_PART" ]; then
  echo "Error: new partition $DATA_PART did not appear. Exiting."
  exit 1
fi

echo "Formatting $DATA_PART as exFAT with label $DATA_LABEL..."
mkfs.exfat -n "$DATA_LABEL" "$DATA_PART"

# 4. Copying the offline content
echo "Mounting $DATA_PART to copy offline content..."
MOUNT_POINT=$(mktemp -d)
mount "$DATA_PART" "$MOUNT_POINT"
trap 'umount "$MOUNT_POINT" 2>/dev/null; rmdir "$MOUNT_POINT" 2>/dev/null' EXIT

echo "Copying content... (This will take a very long time depending on your dataset size)"
# Partial .part downloads are copied too, so the updater can resume them from the stick
if [ -d "content" ]; then
  cp -r content "$MOUNT_POINT/"
fi
if [ -d "readers" ]; then
  # The glob skips readers/.downloads, the cache get_readers.sh keeps
  mkdir -p "$MOUNT_POINT/readers"
  cp -r readers/* "$MOUNT_POINT/readers/"
fi
for f in updater.py manifest.json VERSION; do
  if [ -f "$f" ]; then
    cp "$f" "$MOUNT_POINT/"
  fi
done

# Ensure everything is written to disk
echo "Flushing writes to the USB drive..."
sync

echo "================================================="
echo " Build Complete!"
echo " Your Lighthouse USB is ready."
echo " Plug it into any PC to boot the Live OS,"
echo " or open the $DATA_LABEL drive on any computer or phone."
echo "================================================="

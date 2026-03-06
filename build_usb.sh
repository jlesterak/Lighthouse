#!/bin/bash
# Lighthouse USB Builder Script
# WARNING: This script performs destructive operations on the specified block device.
# It flashes the Live OS ISO and creates an exFAT partition in the remaining space.

set -e

if [ "$EUID" -ne 0 ]; then
  echo "Please run this script as root (sudo)."
  exit 1
fi

if [ -z "$1" ]; then
  echo "Usage: sudo $0 /dev/sdX [amd64|arm64]"
  echo "Replace /dev/sdX with your USB drive device name."
  echo "Run 'lsblk' to find the correct device. DO NOT guess."
  echo "Architecture defaults to amd64 if not provided."
  exit 1
fi

DEVICE=$1
TARGET_ARCH=${2:-amd64}
ISO_FILE="LiveOS/live-image-${TARGET_ARCH}.hybrid.iso"

# Check if the device exists and is a block device
if [ ! -b "$DEVICE" ]; then
  echo "Error: Device $DEVICE not found or is not a physical block device."
  exit 1
fi

# Basic sanity check to avoid wiping root drive (sda/nvme0n1 usually)
if [[ "$DEVICE" == *"/dev/sda"* ]] || [[ "$DEVICE" == *"/dev/nvme0n1"* ]]; then
  echo "WARNING: You specified $DEVICE, which looks like a primary hard drive."
  read -p "Are you ABSOLUTELY SURE you want to completely wipe $DEVICE? (type 'yes-wipe'): " confirmation
  if [ "$confirmation" != "yes-wipe" ]; then
    echo "Aborting."
    exit 1
  fi
fi

# Verify ISO exists
if [ ! -f "$ISO_FILE" ]; then
  echo "Error: $ISO_FILE not found. Please build the Live OS first."
  echo "cd LiveOS && sudo lb build"
  exit 1
fi

echo "================================================="
echo " Lighthouse USB Flasher"
echo "================================================="
echo "Target Device: $DEVICE"
echo "Target ISO:    $ISO_FILE"
echo ""
echo "WARNING: ALL DATA ON $DEVICE WILL BE DESTROYED."
echo "================================================="
read -p "Press ENTER to continue, or Ctrl+C to abort..."

# 1. Unmount any existing partitions
echo "Unmounting any existing partitions on $DEVICE..."
umount ${DEVICE}* 2>/dev/null || true

# 2. Flash the Live ISO
echo "Flashing Live ISO to $DEVICE using dd..."
echo "(This may take a few minutes depending on your USB speed)"
dd if=$ISO_FILE of=$DEVICE bs=4M status=progress
sync

# 3. Create a new partition in the remaining space
echo "Creating exFAT data partition in the remaining free space..."

# Get the last sector used by the ISO to know where to start the new partition
# sfdisk will drop the partition at the end of the free space if we just tell it to create a new one.

# Since `dd` writes a hybrid MBR/GPT or ISO9660, Linux tools like `parted` or `fdisk` can be tricky.
# We use fdisk to create a new primary partition (usually #3) taking up the rest of the disk.
# Echoing commands to fdisk:
# n: new partition
# p: primary
# (default partition number, usually 3)
# (default start sector)
# (default end sector)
# t: change type
# (partition number)
# 7: HPFS/NTFS/exFAT
# w: write and exit

echo -e "n\np\n\n\n\nt\n\n7\nw" | fdisk $DEVICE >/dev/null 2>&1 || true
sync

# The new partition might be part 3 or 2 depending on the hybrid ISO format. Let's find it.
# We will wait for the OS to re-read partition tables
partprobe $DEVICE || true
sleep 3

# Find exactly which partition was just created (should be the last one)
DATA_PART_NAME=$(lsblk -rn -o NAME "$DEVICE" | tail -n 1)
DATA_PART="/dev/$DATA_PART_NAME"

if [ ! -b "$DATA_PART" ] || [ "$DATA_PART" == "$DEVICE" ]; then
    echo "Error: Could not determine newly created partition. Exiting."
    exit 1
fi

echo "Formatting $DATA_PART as exFAT with label LIGHTHOUSE..."
mkfs.exfat -n LIGHTHOUSE $DATA_PART

# 4. Copying the offline content
echo "Mounting $DATA_PART to copy offline content..."
MOUNT_POINT=$(mktemp -d)
mount $DATA_PART $MOUNT_POINT

echo "Copying content... (This will take a very long time depending on your dataset size)"
if [ -d "content" ]; then
    cp -r content "$MOUNT_POINT/"
fi
if [ -d "readers" ]; then
    cp -r readers "$MOUNT_POINT/"
fi
if [ -f "updater.py" ]; then
    cp updater.py "$MOUNT_POINT/"
fi
if [ -f "manifest.json" ]; then
    cp manifest.json "$MOUNT_POINT/"
fi

# Ensure everything is written to disk
sync

umount $MOUNT_POINT
rm -rf $MOUNT_POINT

echo "================================================="
echo " Build Complete!"
echo " Your Lighthouse USB is ready."
echo " Plug it into any PC to boot the Live OS,"
echo " or access the files natively from the format."
echo "================================================="

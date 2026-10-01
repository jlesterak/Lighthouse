#!/bin/bash
# Lighthouse USB Builder Script
# WARNING: This script performs destructive operations on the specified block device.
# It flashes the Live OS ISO and creates an exFAT partition in the remaining space.
#
# Layout: [ ISO (hybrid: iso9660 + EFI image) | room to grow | persistence | LIGHTHOUSE exFAT data ]
# Everything after the ISO starts at OS_RESERVE_GIB (default 4 GiB), not right after the ISO, so a
# newer, bigger ISO can later be written in place with --update-os without touching the data.
#
# Modes:
#   sudo ./build_usb.sh /dev/sdX [amd64|arm64]               wipe and build a new stick
#   sudo ./build_usb.sh --update-os /dev/sdX [amd64|arm64]   replace only the Live OS; keep
#        the LIGHTHOUSE partition and everything on it (content, persistence)
#
# Persistence: a fresh stick gets an ext4 partition labelled "persistence" (PERSIST_GIB, default
# 4) with persistence.conf "/ union". The Live OS boots with the "persistence" option and keeps
# settings, Wi-Fi passwords and installed packages there; the failsafe boot entry ignores it.
# A partition, not a file on LIGHTHOUSE: live-boot opens persistence before exFAT support is
# loaded, and a root mount of LIGHTHOUSE would leave the user unable to write to it. Its MBR
# type is 83 (Linux), which Windows doesn't mount, so no "format this disk?" prompt.
# PERSIST_GIB=0 skips it.

set -euo pipefail

cd "$(dirname "$0")"

# Must match LABEL in LiveOS/.../lighthouse-mount.sh (exFAT labels max out at 11 chars)
DATA_LABEL="LIGHTHOUSE"
OS_RESERVE_GIB=${OS_RESERVE_GIB:-4}
PERSIST_GIB=${PERSIST_GIB:-4}

UPDATE_OS=0
if [ "${1:-}" = "--update-os" ]; then
  UPDATE_OS=1
  shift
fi

if [ "$EUID" -ne 0 ]; then
  echo "Please run this script as root (sudo)."
  exit 1
fi

if [ -z "${1:-}" ]; then
  echo "Usage: sudo $0 [--update-os] /dev/sdX [amd64|arm64]"
  echo "  --update-os  replace only the Live OS and keep the $DATA_LABEL partition"
  echo "Replace /dev/sdX with your USB drive device name."
  echo "Run 'lsblk' to find the correct device. DO NOT guess."
  echo "Architecture defaults to amd64 if not provided."
  exit 1
fi

DEVICE=$1
TARGET_ARCH=${2:-amd64}
ISO_FILE=${ISO_FILE:-"LiveOS/live-image-${TARGET_ARCH}.hybrid.iso"}

for cmd in lsblk sfdisk partprobe mkfs.exfat mkfs.ext4 udevadm blkid; do
  if ! command -v "$cmd" &> /dev/null; then
    echo "Error: '$cmd' not found. Install with: sudo apt install util-linux fdisk parted exfatprogs e2fsprogs"
    exit 1
  fi
done

# Check if the device exists and is a whole disk, not a partition
if [ ! -b "$DEVICE" ]; then
  echo "Error: Device $DEVICE not found or is not a physical block device."
  exit 1
fi
# (loop devices count, so the whole flow can be tested on an image file)
DEVICE_TYPE=$(lsblk -dno TYPE "$DEVICE")
if [ "$DEVICE_TYPE" != "disk" ] && [ "$DEVICE_TYPE" != "loop" ]; then
  echo "Error: $DEVICE is not a whole disk. Give the disk (e.g. /dev/sdb), not a partition (/dev/sdb1)."
  exit 1
fi

# Never touch a disk holding the running system, whatever its name
SYSTEM_MOUNTS=$(lsblk -nro MOUNTPOINT "$DEVICE" | grep -xE '/|/boot|/boot/efi|/home|/usr|/var|\[SWAP\]' || true)
if [ -n "$SYSTEM_MOUNTS" ]; then
  echo "Error: $DEVICE holds the running system (mounted at: $(paste -sd' ' <<< "$SYSTEM_MOUNTS")). Refusing to wipe it."
  exit 1
fi

# Anything that isn't a removable USB device gets an extra, explicit confirmation
REMOVABLE=$(lsblk -dno RM "$DEVICE" | tr -d ' ')
TRANSPORT=$(lsblk -dno TRAN "$DEVICE" | tr -d ' ')
if [ "$REMOVABLE" != "1" ] && [ "$TRANSPORT" != "usb" ]; then
  echo "WARNING: $DEVICE is not a removable USB device (transport: ${TRANSPORT:-unknown})."
  echo "It looks like an internal drive."
  if [ "$UPDATE_OS" -eq 1 ]; then what="overwrite the Live OS area of"; else what="completely wipe"; fi
  read -r -p "Are you ABSOLUTELY SURE you want to $what $DEVICE? (type 'yes-wipe'): " confirmation
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

ISO_BYTES=$(stat -c %s "$ISO_FILE")

# --update-os: write the new ISO over the OS area only, then put the data partition's
# table entry back exactly as it was (dd replaces the partition table with the ISO's own).
if [ "$UPDATE_OS" -eq 1 ]; then
  # Every partition we must keep (data, and persistence if present), in disk order
  KEEP_LINES=$(sfdisk -d "$DEVICE" | grep '^/dev/' | while read -r line; do
    part=${line%% *}
    case "$(blkid -s LABEL -o value "$part" 2>/dev/null)" in
      "$DATA_LABEL"|persistence) echo "$line" ;;
    esac
  done | sort -t= -k2 -n)
  KEEP_LABELS=$(lsblk -nro LABEL "$DEVICE" | grep -xE "$DATA_LABEL|persistence" || true)
  if ! grep -qx "$DATA_LABEL" <<< "$KEEP_LABELS"; then
    echo "Error: no $DATA_LABEL partition on $DEVICE. Build the stick without --update-os first."
    exit 1
  fi
  DATA_START=$(sed -E 's/.*start= *([0-9]+).*/\1/' <<< "$KEEP_LINES" | sort -n | head -n 1)
  DATA_START_BYTES=$(( DATA_START * 512 ))
  if [ "$ISO_BYTES" -gt "$DATA_START_BYTES" ]; then
    echo "Error: the new ISO ($ISO_BYTES bytes) is bigger than the space before the $DATA_LABEL"
    echo "partition ($DATA_START_BYTES bytes). Writing it would destroy the start of your data."
    echo "This stick predates the OS reserve: back up the $DATA_LABEL contents and rebuild it."
    exit 1
  fi
  echo "================================================="
  echo " Lighthouse OS update (data is kept)"
  echo "================================================="
  lsblk -o NAME,SIZE,FSTYPE,LABEL,MOUNTPOINT "$DEVICE"
  echo ""
  echo "New ISO: $ISO_FILE ($(( ISO_BYTES / 1048576 )) MiB) into $(( DATA_START_BYTES / 1048576 )) MiB of OS space."
  echo "Kept partitions (data must start at or after sector $DATA_START):"
  sed 's/^/  /' <<< "$KEEP_LINES"
  read -r -p "Type the device name ($DEVICE) to continue, or anything else to abort: " confirm_device
  if [ "$confirm_device" != "$DEVICE" ]; then
    echo "Aborting."
    exit 1
  fi
  { lsblk -nro MOUNTPOINT "$DEVICE" | grep -v '^$' || true; } | while read -r mp; do
    umount "$mp"
  done
  dd if="$ISO_FILE" of="$DEVICE" bs=4M status=progress conv=fsync
  partprobe "$DEVICE" || true
  udevadm settle
  # Re-add each kept partition exactly where it was, in disk order (same start, size, type)
  while read -r line; do
    st=$(sed -E 's/.*start= *([0-9]+).*/\1/' <<< "$line")
    sz=$(sed -E 's/.*size= *([0-9]+).*/\1/' <<< "$line")
    ty=$(sed -E 's/.*type= *([0-9a-fA-F]+).*/\1/' <<< "$line")
    echo "${st},${sz},${ty}" | sfdisk --append --no-reread "$DEVICE"
  done <<< "$KEEP_LINES"
  partprobe "$DEVICE" || true
  udevadm settle
  sleep 1
  missing=""
  for want in $KEEP_LABELS; do
    lsblk -nro LABEL "$DEVICE" | grep -qx "$want" || missing="$missing $want"
  done
  if [ -n "$missing" ]; then
    echo "Error: partition(s)$missing did not come back. The entries to restore were:"
    sed 's/^/  /' <<< "$KEEP_LINES"
    echo "Re-add each with: echo 'START,SIZE,TYPE' | sudo sfdisk --append $DEVICE"
    exit 1
  fi
  sync
  echo "OS updated. Kept:"; lsblk -o NAME,SIZE,FSTYPE,LABEL "$DEVICE"
  exit 0
fi

# Warn early if the content can't possibly fit
DISK_BYTES=$(lsblk -dbno SIZE "$DEVICE")
CONTENT_BYTES=$( (du -scb content readers 2>/dev/null || true) | tail -n 1 | cut -f1)
OS_RESERVE_BYTES=$(( OS_RESERVE_GIB * 1073741824 ))
if [ "$ISO_BYTES" -gt "$OS_RESERVE_BYTES" ]; then
  echo "Error: the ISO ($(( ISO_BYTES / 1048576 )) MiB) is bigger than OS_RESERVE_GIB=$OS_RESERVE_GIB. Raise OS_RESERVE_GIB."
  exit 1
fi
NEED_BYTES=$(( OS_RESERVE_BYTES + CONTENT_BYTES + PERSIST_GIB * 1073741824 ))
if [ "$NEED_BYTES" -gt "$DISK_BYTES" ]; then
  echo "Error: OS space + content + persistence need $(( NEED_BYTES / 1000000000 )) GB, but $DEVICE is only $(( DISK_BYTES / 1000000000 )) GB."
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
# Start after the OS reserve (in 512-byte sectors), so later ISOs can grow into the gap.
# Persistence (type 83) first, then the exFAT data partition (type 7) in the rest.
NEXT=$(( OS_RESERVE_BYTES / 512 ))
new_parts=1
if [ "$PERSIST_GIB" -gt 0 ]; then
  echo "${NEXT},$(( PERSIST_GIB * 1073741824 / 512 )),83" | sfdisk --append --no-reread "$DEVICE"
  NEXT=$(( NEXT + PERSIST_GIB * 1073741824 / 512 ))
  new_parts=2
fi
echo "${NEXT},,7" | sfdisk --append --no-reread "$DEVICE"
parts_after=$(sfdisk -d "$DEVICE" | grep -c '^/dev/' || true)
if [ "$parts_after" -ne "$(( parts_before + new_parts ))" ]; then
  echo "Error: expected $new_parts new partition(s) (had $parts_before, now $parts_after). Exiting."
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

if [ "$PERSIST_GIB" -gt 0 ]; then
  PERSIST_PART=$(sfdisk -d "$DEVICE" | grep '^/dev/' | tail -n 2 | head -n 1 | cut -d' ' -f1)
  echo "Formatting $PERSIST_PART as ext4 with label persistence..."
  mkfs.ext4 -q -F -L persistence "$PERSIST_PART"
  PMNT=$(mktemp -d)
  mount "$PERSIST_PART" "$PMNT"
  echo "/ union" > "$PMNT/persistence.conf"
  umount "$PMNT"; rmdir "$PMNT"
fi

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

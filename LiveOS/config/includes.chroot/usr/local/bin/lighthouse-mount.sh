#!/bin/bash
# Lighthouse Data Auto-Mounter
# Finds the exFAT partition labeled LIGHTHOUSE and mounts it
# to a known path so the desktop and users can easily access it.

# Must match the label build_usb.sh gives the partition (exFAT labels max out at 11 chars)
LABEL="LIGHTHOUSE"
MOUNT_DIR="/media/LighthouseData"
LIVE_USER="user"

mkdir -p "$MOUNT_DIR"

if mountpoint -q "$MOUNT_DIR"; then
    echo "$MOUNT_DIR is already mounted."
    exit 0
fi

# Wait for devices to settle, then give slow USB sticks up to 30s to show up
udevadm settle --timeout=30 || true
DEV_PATH=""
for _ in $(seq 1 30); do
    DEV_PATH=$(blkid -L "$LABEL")
    [ -n "$DEV_PATH" ] && break
    sleep 1
done

if [ -z "$DEV_PATH" ]; then
    echo "$LABEL partition not found. Is this booted from the Lighthouse USB?"
    exit 0
fi

echo "Found Lighthouse Data partition at $DEV_PATH"

# live-config creates the live user during boot; mount with its uid/gid
USER_UID=$(id -u "$LIVE_USER" 2>/dev/null || echo 1000)
USER_GID=$(id -g "$LIVE_USER" 2>/dev/null || echo 1000)

if ! mount -t exfat -o "uid=$USER_UID,gid=$USER_GID,umask=022" "$DEV_PATH" "$MOUNT_DIR"; then
    echo "Failed to mount $DEV_PATH"
    exit 1
fi
echo "Successfully mounted to $MOUNT_DIR"

# Create a shortcut on the Desktop for easy access
USER_HOME=$(getent passwd "$LIVE_USER" | cut -d: -f6)
if [ -n "$USER_HOME" ] && [ -d "$USER_HOME" ]; then
    mkdir -p "$USER_HOME/Desktop"
    chown "$USER_UID:$USER_GID" "$USER_HOME/Desktop"
    ln -sfn "$MOUNT_DIR" "$USER_HOME/Desktop/Lighthouse_Knowledge_Base"
    chown -h "$USER_UID:$USER_GID" "$USER_HOME/Desktop/Lighthouse_Knowledge_Base"
fi

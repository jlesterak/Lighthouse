#!/bin/bash
# Lighthouse Data Auto-Mounter
# Finds the exFAT partition labeled LIGHTHOUSE_DATA and mounts it
# to a known path so the desktop and users can easily access it.

MOUNT_DIR="/media/LighthouseData"
mkdir -p "$MOUNT_DIR"

# Wait for devices to settle
sleep 5

# Find the block device by label
DEV_PATH=$(blkid -L LIGHTHOUSE_DATA)

if [ -n "$DEV_PATH" ]; then
    echo "Found Lighthouse Data partition at $DEV_PATH"
    
    # Mount it with user permissions (uid 1000 is the default 'user' on Debian Live)
    mount -t exfat -o uid=1000,gid=1000,umask=000 "$DEV_PATH" "$MOUNT_DIR"
    
    if [ $? -eq 0 ]; then
        echo "Successfully mounted to $MOUNT_DIR"
        
        # Create a symlink on the Desktop for easy access
        ln -sf "$MOUNT_DIR" "/home/user/Desktop/Lighthouse_Knowledge_Base"
        chown -h 1000:1000 "/home/user/Desktop/Lighthouse_Knowledge_Base"
    else
        echo "Failed to mount $DEV_PATH"
    fi
else
    echo "LIGHTHOUSE_DATA partition not found. Is this booted from the Lighthouse USB?"
fi

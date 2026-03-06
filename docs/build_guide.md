# Lighthouse Build Guide

This guide will walk you through the process of building the Lighthouse USB from scratch on a Linux machine.

> [!WARNING]
> Building the bootable USB involves destructive disk operations (`fdisk`, `mkfs.exfat`). Be extremely careful to select the correct USB drive, or you will overwrite your primary hard drive!

## Prerequisites

1. A Debian-based Linux distribution (Ubuntu, Debian, Linux Mint) to run the build scripts.
2. At least 200GB of free disk space for downloading the `.zim` files and building the Live ISO.
3. A USB Drive (128GB minimum, 256GB recommended for the full Wikipedia dump).
4. Required dependencies:
   ```bash
   sudo apt update
   sudo apt install git live-build fdisk exfat-fuse exfat-utils python3 jq
   ```

## Step 1: Clone the Repository

Clone the project to your local machine:

```bash
git clone https://github.com/yourusername/Lighthouse.git
cd Lighthouse
```

## Step 2: Download the Knowledge Base

Before we build the USB, we need to download the knowledge base and the cross-platform reader software.

1. **Launch the Master Setup Script:** We provide a unified wrapper script to handle downloading resources and assembling the USB.
   ```bash
   ./setup.sh
   ```

2. **Download Readers & Content:** Choose Option **1** and Option **2** from the interactive menu to download the ZIM offline libraries and Kiwix reader software.

## Step 3: Build the Live OS ISO

Lighthouse uses Debian's `live-build` toolchain to construct a customized XFCE Live environment featuring Kiwix and Marble (Offline Maps).

1. From the `setup.sh` interactive menu, choose Option **3** (Build Live OS ISO).
2. The script will automatically trigger `build_iso.sh` as root, download the base Debian packages, and assemble the `.iso` file. This process can take 30-60 minutes.
3. Once completed, you will find a file named `live-image-amd64.hybrid.iso` inside the `LiveOS/` directory.

## Step 4: Flash the USB Drive

Finally, we must partition and format the physical USB drive to accept both the bootable Live OS and the `exFAT` cross-platform data partition.

1. **Identify your USB Drive:** Plug in your USB stick and locate its block device name in a separate terminal.
   ```bash
   lsblk
   ```
   > [!CAUTION]
   > Identify the correct `/dev/sdX` device (e.g., `/dev/sdb` or `/dev/sdc`). Do not confuse this with your main drive (usually `/dev/sda` or `/dev/nvme0n1`).

2. **Run the Automated Script:** Return to the `setup.sh` menu and choose Option **4** (Flash Live OS & Content to USB).
3. The script will prompt you for the `/dev/sdX` target. Enter the block device path you found earlier.

### What does `build_usb.sh` do?
- It wipes the partition table of `/dev/sdX`.
- It uses `dd` to flash the custom `live-image-amd64.hybrid.iso` to the start of the drive.
- It calculates the remaining free space on the USB stick.
- It creates a new `exFAT` partition in that free space.
- It mounts the new partition and copies over your `content/` folder, `readers/` folder, and `updater.py` tool.

Once the script completes, your Lighthouse USB is fully operational and ready to be stored in your emergency kit.

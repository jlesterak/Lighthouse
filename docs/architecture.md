# Lighthouse Architecture

Lighthouse combines several specialized technologies to create a resilient, offline knowledge repository that is accessible regardless of the host machine's operating system, while also doubling as its own standalone operating system.

## 1. The Data Format (`.zim`)

At the core of Lighthouse is the **ZIM** (Zeno IMproved) file format. ZIM is an open standard designed specifically to store wiki content for offline usage. Developed by the [Kiwix](https://www.kiwix.org/) project, ZIM files compress millions of HTML pages, images, and search indexes into a single, highly optimized binary file.

Lighthouse leverages this ecosystem heavily. We provide the Kiwix desktop and mobile readers, and download the `.zim` files directly from Kiwix servers.

## 2. The Physical USB Layout

The most complex requirement of Lighthouse is that the USB drive must be:
1. Bootable as a Live Linux OS on standard PC hardware.
2. Readable and writable by Windows, macOS, Linux, and Android (via an OTG adapter) when plugged in as a standard storage drive.

To achieve this, the USB drive is partitioned into two distinct volumes:

### Partition 1: The Boot Partition (Hybrid ISO9660 / FAT32 / ext4)
- Contains the GRUB/Syslinux bootloader.
- Contains the compressed `squashfs` filesystem of the Debian Live OS.
- This partition is flashed directly from the customized `.iso` image built by `live-build`.
- *Note: Windows will often prompt the user to "format" this partition because it doesn't understand the filesystem structure. Users must ignore this prompt.*

### Partition 2: The Data Partition (`exFAT`)
- `exFAT` is chosen because it supports files larger than 4GB (crucial for `.zim` files like Wikipedia, which routinely exceed 50GB) and is natively supported by Windows, macOS, recent Linux kernels, and most Android devices.
- This is the partition the user interacts with.
- **Contents:**
  - `Readers/` - Packaged Kiwix binaries (Windows `.exe`, Linux AppImage, Android `.apk`).
  - `Content/` - The `.zim` libraries and PDFs downloaded by the updater.
  - `Updater/` - The `updater.py` script and the `manifest.json`.

During the boot process of the Live OS, a custom init script or systemd service mounts a designated `exFAT` partition with the label `LIGHTHOUSE_DATA` so that the desktop environment instantly has access to the stored knowledge.

## 3. The Custom Live OS (`live-build`)

The bootable operating system is explicitly generated using Debian's `live-build` toolchain.

- **Base:** Debian Stable (`bookworm` or newer).
- **Desktop Environment:** XFCE (chosen for extremely low memory usage, allowing it to run on older or lower-spec hardware).
- **Customizations:**
  - `kiwix-desktop` is pre-installed.
  - `aria2` and `python3` are included for running the updater tools from within the live environment.
  - The desktop background is customized to display clear visual instructions on how to use the software.

## 4. The Updater Workflow (`updater.py`)

Because Lighthouse is designed for users preparing for off-grid or emergency scenarios, the internet connections available for downloading massive datasets may be highly unstable (satellite internet, weak 4G/LTE/Ham mesh, etc.).

Standard tools like `wget` or `curl` can resume downloads, but often require specific flags or struggle on certain platforms. To ensure cross-platform compatibility, Lighthouse provides a custom Python script relying *only* on the standard library.

### Resilient Downloading
The `updater.py` tool utilizes HTTP `Range` headers. When starting a download:
1. It queries the server for the total file size (`Content-Length`).
2. It checks if the file already exists locally. If it does, it checks the local file's byte size.
3. It sends a request with the header `Range: bytes={LOCAL_SIZE}-`
4. The server responds with HTTP 206 (Partial Content), and the script appends the incoming stream directly to the file on disk.

This allows the user to simply re-run `python3 updater.py` if their connection drops, and the download instantly resumes from the exact byte it failed on.

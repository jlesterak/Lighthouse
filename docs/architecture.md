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
  - `readers/` - Packaged Kiwix binaries (`windows/kiwix-desktop.exe`, `kiwix-desktop.AppImage`, `kiwix-android.apk`) and `VERSIONS.txt`.
  - `content/` - The `.zim` libraries downloaded by the updater (including any `.part` files, which resume from the stick).
  - `updater.py` and `manifest.json` at the top level. Running `python3 updater.py` from the stick downloads straight into its `content/` folder, because the updater resolves paths relative to itself.

During the boot process of the Live OS, a systemd service (`lighthouse-mount.service`, enabled by a live-build hook) mounts the `exFAT` partition labeled `LIGHTHOUSE` at `/media/LighthouseData` and puts a `Lighthouse_Knowledge_Base` shortcut on the desktop, so that the desktop environment instantly has access to the stored knowledge.

## 3. The Custom Live OS (`live-build`)

The bootable operating system is explicitly generated using Debian's `live-build` toolchain.

- **Base:** Debian Stable (`bookworm` or newer).
- **Desktop Environment:** XFCE (chosen for extremely low memory usage, allowing it to run on older or lower-spec hardware).
- **Customizations:**
  - Kiwix is pre-installed: the `kiwix` package (kiwix-desktop) to read ZIMs, and `kiwix-tools` for `kiwix-serve`, which shares the library over the local network.
  - `aria2` and `python3` are included for running the updater tools from within the live environment.
  - The desktop background is customized to display clear visual instructions on how to use the software.

## 4. The Unified Orchestrator (`setup.sh`)

Lighthouse provides a simple, interactive `setup.sh` orchestrator script. This single entrypoint allows users to build the entire project locally without needing to manually invoke the underlying bash/python scripts mapping to individual components (`build_iso.sh`, `updater.py`, etc.). The script can be executed securely via `curl` to silently handle bootstrapping the git repository.

## 5. The Updater Workflow (`updater.py`)

Because Lighthouse is designed for users preparing for off-grid or emergency scenarios, the internet connections available for downloading massive datasets may be highly unstable (satellite internet, weak 4G/LTE/Ham mesh, etc.).

Standard tools like `wget` or `curl` can resume downloads, but often require specific flags or struggle on certain platforms. To ensure cross-platform compatibility, Lighthouse provides a custom Python script relying *only* on the standard library.

### Resilient Downloading
The `updater.py` tool utilizes HTTP `Range` headers. When starting a download:
1. It queries the server for the total file size (`Content-Length`).
2. It checks if the file already exists locally. If it does, it checks the local file's byte size.
3. It sends a request with the header `Range: bytes={LOCAL_SIZE}-`
4. The server responds with HTTP 206 (Partial Content), and the script appends the incoming stream directly to the `.part` file on disk.

5. If the server answers 200 instead of 206 (it ignored the `Range` header), the partial file is discarded and the download restarts, so the whole body is never appended to a partial file.
6. If the connection drops or closes before `Content-Length` bytes arrive, the updater retries automatically with exponential backoff (up to 10 tries, capped at 60s), resuming each time. The `.part` file is only renamed to the final `.zim` once it is complete.

7. Once complete, the file is checked against the SHA-256 that Kiwix publishes next to every ZIM (`<file>.sha256`). A mismatch deletes the corrupt download rather than leaving a broken library on the stick; if no checksum is published, the updater says so and keeps the file.

If it does give up, the user can simply re-run `python3 updater.py` later, and the download resumes from the exact byte it stopped on.

### Catalog lookup
Manifest items name a Kiwix catalog `name` and `flavour` rather than a fixed URL, since Kiwix publishes new dated releases (`wikipedia_en_all_maxi_2026-08.zim`) and removes old ones. The updater queries `https://library.kiwix.org/catalog/v2/entries?name=<name>` (an exact match), picks the entry with the matching flavour, and downloads the ZIM behind its Metalink link.

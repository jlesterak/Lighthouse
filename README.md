# Project Lighthouse

**Lighthouse** is a comprehensive, free and open-source project designed to create a bootable USB drive containing a vast offline repository of critical human knowledge. Built with off-grid living, doomsday prepping, and emergency situations in mind, Lighthouse ensures that reliable information and the tools to access it are always available, even when the internet is not.

## Features

- **Massive Offline Library:** Houses complete, compressed copies (via ZIM files) of Wikipedia, Wikimed, Stack Exchanges, computing resources, ham radio guides, and survival manuals.
- **Cross-Platform Accessibility:** Includes pre-packaged, standalone Kiwix readers for Windows (Portable), Linux (AppImage), and Android (APK). You never need an internet connection to install the reader software.
- **Bootable Live OS:** Doubles as a bootable Live USB running a customized, lightweight Debian Linux environment (XFCE) pre-configured with all necessary tools to read and parse the data repository natively.
- **Resilient Updater:** Features a custom, Python-based updater tool designed specifically for spotty internet connections. It allows users to select specific knowledge categories and seamlessly resume interrupted downloads byte-for-byte.

## Repository Structure

```text
Lighthouse/
├── content/              # The offline data repository (ZIMs, PDFs)
├── readers/              # Standalone Kiwix binaries for Windows, Linux, Android
├── docs/                 # Extensive project documentation
│   ├── architecture.md   # System design and USB partition layout
│   ├── build_guide.md    # Instructions on how to compile the USB yourself
│   └── user_guide.md     # How to use the Updater and Readers
├── LiveOS/               # Debian live-build configuration for the bootable OS
├── updater.py            # The cross-platform resilient download tool
├── manifest.json         # The catalog of available FOSS knowledge repositories
├── build_iso.sh          # The automated script to build the Live OS ISO
├── build_usb.sh          # The automated script to format and build the USB drive
├── get_readers.sh        # Utility script to download the Kiwix binaries
├── LICENSE               # GPLv3 Open Source License
└── CONTRIBUTING.md       # Guidelines for contributing to Lighthouse
```

## Getting Started

To build your own Lighthouse drive, or simply download the offline resources to your local machine:

1. Clone this repository:
   ```bash
   git clone https://github.com/jlesterak/Lighthouse.git
   cd Lighthouse
   ```
2. Run the updater to fetch your desired offline content:
   ```bash
   python3 updater.py
   ```
3. Fetch the offline readers:
   ```bash
   ./get_readers.sh
   ```
4. If building the full bootable USB, consult the [Build Guide](docs/build_guide.md).

## Philosophy and License

Lighthouse is built entirely upon Free and Open Source Software (FOSS). It relies heavily on the incredible work of the [Kiwix](https://www.kiwix.org/) project. 

This project is licensed under the [GNU General Public License v3.0](LICENSE).

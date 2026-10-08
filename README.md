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
├── VERSION               # The project version (single source of truth)
├── manifest.json         # The catalog of available FOSS knowledge repositories
├── build_iso.sh          # The automated script to build the Live OS ISO
├── build_usb.sh          # The automated script to format and build the USB drive
├── get_readers.sh        # Utility script to download the Kiwix binaries
├── tools/                # Turn your own manuals into ZIMs (pdf2zim.py, site2zim.py)
├── tests/                # Test suite (python3 -m unittest discover -s tests)
├── CHANGELOG.md          # Release history
├── LICENSE               # GPLv3 Open Source License
└── CONTRIBUTING.md       # Guidelines for contributing to Lighthouse (incl. releases)
```

## Getting Started

To build your own Lighthouse drive, or simply download the offline resources to your local machine, use the interactive Setup Script:

```bash
bash <(curl -sL https://raw.githubusercontent.com/jlesterak/Lighthouse/master/setup.sh)
```

The script will automatically clone the repository (if necessary) and present a guided menu to:
1. Download Offline Content (Wikipedia, Medical Guides, Maps, etc.)
2. Download Readers (Kiwix for Desktop, Linux, and Android)
3. Build the bootable Live OS ISO
4. Format and flash the Live OS & Knowledge Base to a USB Drive

If building the full bootable Live OS manually, consult the [Build Guide](docs/build_guide.md).

## Recommended ZIMs

The updater offers everything in `manifest.json`: Wikipedia, WikiMed, the medical library, CD3WD, iFixit, the
zimgit post-disaster, water and food sets, the ServerFault, AskUbuntu, Electronics and Ham Radio Stack Exchanges,
and the OpenStreetMap wiki. These are also worth adding from the [Kiwix library](https://library.kiwix.org/):

| ZIM (catalog name) | Why |
|---|---|
| `mechanics.stackexchange.com_en_all` | Motor vehicle maintenance and repair Q&A |
| `diy.stackexchange.com_en_all` | Home improvement: wiring, plumbing, carpentry |
| `gardening.stackexchange.com_en_all` | Growing food |
| `outdoors.stackexchange.com_en_all` | Camping, navigation, wilderness skills |
| `cooking.stackexchange.com_en_all` | Food preparation and preservation |
| `appropedia_en_all` | Appropriate technology, sustainability, off-grid builds |
| `gutenberg_en_all` | Project Gutenberg's public-domain books (very large) |
| `wiktionary_en_all` | Dictionary |

## Your Own Manuals

The ZIMs above don't cover the specific machines you own. `tools/` converts the manuals you have into ZIMs, so
they get Kiwix search on any reader, including a phone with no signal:

- **`tools/pdf2zim.py`**: a bookmarked PDF (a service manual, a device manual). Each bookmark becomes an article
  showing the page images plus their text.
- **`tools/site2zim.py`**: a static HTML site, as a folder or a `.zip`. It recognizes the offline zips from
  [LEMON Manuals](https://lemon-manuals.la), which carry factory-style repair information for most US and Canadian
  vehicles from 1960 to 2025: color wiring diagrams, connector views, TSBs, DTC indexes, specs and labor
  times. Pick your vehicle by year, model and **engine code** (the 8th character of a VIN on most US
  vehicles), download the zip and run:

  ```bash
  pip install libzim pillow
  tools/site2zim.py "LEMON 2016 Ford F-150 XLT, 4D Pickup Extra Cab, 3.5L Eng VIN G, 4WD.zip"
  ```

  No options are needed. The title, name and output file come from the manual itself, and pages about other trims
  are kept out of title suggestions. Copy the `.zim` into `content/` on the stick.

Only convert material you're entitled to keep a copy of, and don't publish what isn't yours to share.

## Philosophy and License

Lighthouse is built entirely upon Free and Open Source Software (FOSS). It relies heavily on the incredible work of the [Kiwix](https://www.kiwix.org/) project. 

This project is licensed under the [GNU General Public License v3.0](LICENSE).

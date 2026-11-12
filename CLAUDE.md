# Lighthouse (offline knowledge USB / ISO)

Public GitHub repo (`origin`). Unlicense. No secrets or private hostnames in commits.

- Builds a bootable live USB/ISO with offline knowledge (ZIM files and readers). Scripts: `setup.sh`, `build_iso.sh`, `build_usb.sh`, `get_readers.sh`; `updater.py` refreshes content from `manifest.json`; `VERSION` drives the release.
- Big state is gitignored and regenerable: `content/`, `readers/`, `dist/` (finished ISOs), `LiveOS/{cache,chroot,binary}` (root-owned live-build output, ~11 GB total). Cleaning `LiveOS` needs sudo, so ask first.
- The stick is also the owner's offline kit; content comes from the owner's kit folders. Keep secrets out of this repo.
- NAEB ethnobotany ZIM: built with `tools/site2zim.py` from a wget mirror (mirror purged 2026-10-29; the ZIM is the keeper).

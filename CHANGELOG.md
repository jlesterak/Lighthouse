# Changelog

All notable changes to Lighthouse. The version number lives in `VERSION`
(the single source of truth) and follows [Semantic Versioning](https://semver.org/).

## [Unreleased]

First real builds of both ISOs, boot-tested in QEMU (amd64 BIOS + UEFI, arm64 UEFI)
and flashed to a real stick.

### Added
- Updater verifies each download against Kiwix's published SHA-256 and deletes a
  corrupt one.
- 5-second auto-boot timeout in syslinux and GRUB, so an unattended stick boots.
- Live OS: Wi-Fi and GPU firmware, terminal, editor, image viewer, gvfs/udisks2.

### Fixed
- Live OS had no live user (`user-setup` was dropped with `--apt-recommends false`),
  so it stopped at a login prompt.
- arm64 ISO had no partition table, so it couldn't boot from a USB stick; the EFI
  image is now added as an ESP.
- An arm64 build after an amd64 one reused the amd64 bootstrap cache.
- Build fails clearly on Ubuntu's old live-build fork, a missing Debian keyring, or
  missing xorriso.
- `build_usb.sh` accepts loop devices (test on an image file); readers are hardlinked
  from their cache.

## [0.2.0] - 2026-09-30

### Added
- Versioning: `VERSION` file read by `updater.py --version`, `setup.sh`, the ISO
  (volume ID and `/etc/lighthouse-release`) and copied onto the USB stick.
- Kiwix (`kiwix`, `kiwix-tools`) in the Live OS, so it can actually open the library.
- Manifest items: iFixit repair guides, post-disaster, water treatment and food
  preparation ZIMs.
- Updater test suite (`tests/`, standard library only).

### Changed
- Manifest items name a Kiwix catalog `catalog_name` + `flavour` instead of `catalog_query`.
- `get_readers.sh` always fetches the latest readers and records `readers/VERSIONS.txt`.
- arm64 builds use grub-efi only and cross-build through qemu-user-static.

### Fixed
- Live OS never mounted the data partition (label mismatch, service never enabled).
- Updater resolved nothing: the Kiwix `root.xml` catalog it parsed is now a stub.
  Five stale catalog names; WikiHow (removed from Kiwix) replaced by iFixit.
- Updater could corrupt or truncate downloads: appended a full body when a server
  ignored `Range`, and finalised files the server cut short. It now retries with backoff.
- Pinned Android reader URL returned 404.
- `build_usb.sh` could format the ISO's EFI partition if partitioning failed, and
  only guarded `/dev/sda` and `/dev/nvme0n1` by name.
- Build output and arm64-pinned generated config were committed to git.

## [0.1.0] - 2026-03-05

Initial Gemini-built version (tagged retroactively): resumable updater with Kiwix catalog
search, manifest, reader fetcher, Debian live-build config for amd64/arm64,
USB flasher, and the `setup.sh` menu.

[Unreleased]: https://github.com/jlesterak/Lighthouse/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/jlesterak/Lighthouse/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/jlesterak/Lighthouse/releases/tag/v0.1.0

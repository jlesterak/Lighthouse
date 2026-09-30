# Changelog

All notable changes to Lighthouse. The version number lives in `VERSION`
(the single source of truth) and follows [Semantic Versioning](https://semver.org/).

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

Initial Gemini-built version (never tagged): resumable updater with Kiwix catalog
search, manifest, reader fetcher, Debian live-build config for amd64/arm64,
USB flasher, and the `setup.sh` menu.

[0.2.0]: https://github.com/jlesterak/Lighthouse/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/jlesterak/Lighthouse/releases/tag/v0.1.0

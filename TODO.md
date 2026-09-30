# Lighthouse TODO

Resumed 2026-09-30 after a break since 2026-03-05 (started with Gemini; now Claude Code).
Findings come from an audit of the code on 2026-09-30.

## [PENDING]

- `get_readers.sh` pins old versions (Android 3.9.2 now 404s) and a hard-coded Windows
  folder name.
- arm64 cross-build: no qemu-user-static/binfmt setup, and syslinux doesn't exist on arm64.
- `build_usb.sh` safety check only matches `/dev/sda` and `/dev/nvme0n1` by name.
- Docs describe `Content/ Readers/ Updater/` on the stick; the script writes
  `content/ readers/` plus loose files.

- (needs a build machine) Build both ISOs end to end and boot them: amd64 in QEMU/real
  hardware, arm64 in QEMU (`qemu-system-aarch64` + UEFI). Nothing in `LiveOS/` has been
  verified by an actual build since the fixes below. Needs `live-build`, and `qemu-user-static`
  for arm64 cross-builds (see `docs/build_guide.md`).
- (needs a spare USB stick) Run `build_usb.sh` on a real stick and confirm the exFAT
  partition mounts on Windows, macOS, Linux, Android, and in the booted Live OS.

## [IN PROGRESS]

## [COMPLETED]

- 2026-09-30: Updater fixed and tested. Catalog lookup uses the exact `?name=` API
  (`root.xml` had become a stub, so nothing resolved); manifest moved to
  `catalog_name` + `flavour` with current names, all 14 items verified live; WikiHow (gone
  from Kiwix) replaced by iFixit, plus post-disaster, water and food-preparation ZIMs.
  Downloads retry with backoff, restart instead of corrupting when a server ignores
  `Range`, never finalise a short file, and use `os.replace`. Paths are relative to the
  script. `tests/test_updater.py` covers all of it (stdlib only, no network).
- 2026-09-30: Live OS ships Kiwix: `kiwix` (kiwix-desktop 2.3.0 in bookworm) and
  `kiwix-tools` (`kiwix-serve`) added to the package list.
- 2026-09-30: Live OS auto-mount fixed: the mount script now looks for `LIGHTHOUSE` (exFAT
  labels max out at 11 chars, so `LIGHTHOUSE_DATA` could never be written), a chroot hook
  enables `lighthouse-mount.service`, and the unit orders after `live-config.service`
  with a retry loop for slow sticks.

- 2026-09-30: Stop tracking live-build output and generated config (`LiveOS/chroot`,
  `LiveOS/.build`, `LiveOS/config/{binary,bootstrap,chroot,common,source}`, stock hook
  symlinks, `__pycache__`). The committed config was pinned to arm64 from the last build.

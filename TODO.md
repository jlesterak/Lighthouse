# Lighthouse TODO

Resumed 2026-09-30 after a break since 2026-03-05 (started with Gemini; now Claude Code).
Findings come from an audit of the code on 2026-09-30.

## [PENDING]

- Data partition label mismatch: `build_usb.sh` writes `LIGHTHOUSE`, the mount script looks
  for `LIGHTHOUSE_DATA`, so the Live OS never mounts the library.
- `lighthouse-mount.service` is copied into the image but never enabled, and it can race
  live-config creating the `user` account and its Desktop.
- Live OS has no ZIM reader: the docs promise Kiwix but the package list lacks it.
- Updater catalog lookup is broken: `catalog/root.xml` is now a 429-byte navigation stub,
  so no manifest item resolves. Five manifest names are also stale (WikiMed → mdwiki,
  CD3WD, WikiHow gone, StackExchange naming).
- Updater robustness: a server that ignores `Range` (200 instead of 206) corrupts the
  file by appending the whole body; the HEAD request has no timeout; `os.rename` fails on
  Windows when the target exists; paths are relative to the working directory.
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

- 2026-09-30: Stop tracking live-build output and generated config (`LiveOS/chroot`,
  `LiveOS/.build`, `LiveOS/config/{binary,bootstrap,chroot,common,source}`, stock hook
  symlinks, `__pycache__`). The committed config was pinned to arm64 from the last build.

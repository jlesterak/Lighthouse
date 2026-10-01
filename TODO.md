# Lighthouse TODO

Resumed 2026-09-30 after a break since 2026-03-05 (started with Gemini; now Claude Code).
Findings come from an audit of the code on 2026-09-30.

## [PENDING]

- 2026-10-01: data partition verified on Linux: picebox mounts the exFAT LIGHTHOUSE partition (UUID 7EBD-D290), and kiwix-serve serves all 5 ZIMs with working full-text search. It now stays plugged into picebox as the LAN library source (http://wiki.lan). Boot and Windows/macOS/Android checks still open.
- 2026-10-01: **amd64 booted on real hardware (Jake) and the library opened.** Wi-Fi said "not ready": the image lacked `wpasupplicant` (recommends are off). Fixed in the package list; needs a rebuild (0.3.0) and a re-test of Wi-Fi.
- 2026-10-01: amd64 ISO rebuilt (wpasupplicant, persistence), build_usb.sh tested 15/15 on a loop device, the 1 TB stick re-flashed with the new layout (OS reserve, 4 GiB persistence, LIGHTHOUSE) and its 27.5 GB of content restored from a verified backup.
- (you) Boot test 2: Wi-Fi connects; reboot and it remembers the network (persistence); failsafe entry boots fresh. arm64 still untested on hardware. Then release 0.3.0 (bump VERSION, rebuild both ISOs, tag).
- (you) Boot the flashed SanDisk stick on real hardware (BIOS and UEFI if you can), and
  open the LIGHTHOUSE partition on Windows, macOS, Android. It holds the amd64 build, the
  readers and 5 test ZIMs (medicine, CD3WD, water, food, ham; all SHA-256 verified).
- After the real-hardware test passes: release 0.3.0 (rename `[Unreleased]` in
  CHANGELOG, bump `VERSION`, rebuild both ISOs so they carry 0.3.0), tag, push.
- (you, sudo) Remove the temporary sudoers rule: `sudo rm /etc/sudoers.d/lighthouse-temp`.

## [IN PROGRESS]

## [COMPLETED]

- 2026-10-01: `tools/site2zim.py`: static HTML sites (folder or .zip, read in place) to ZIMs; LEMON
  Manuals zips need no options (title/name from the front page, other-trim pages kept out of title
  suggestions). Tests in `tests/test_site2zim.py` (skipped without libzim). Built the 2016 F-150
  3.5L EcoBoost (VIN G) manual with it: 627 MB, search and color diagrams verified in kiwix-serve.
  README now lists recommended ZIMs and how to convert your own manuals (pdf2zim, site2zim, LEMON).
- 2026-09-30: Flashed `/dev/sda` (920GB SanDisk, was Ventoy) with the final amd64 build:
  ISO bytes verified on the stick, data partition holds readers, updater, 5 ZIMs.
  Both ISOs kept in `dist/` (gitignored).
- 2026-09-30: arm64 built (cross, ~2h under qemu-user) and boot-tested: `build_usb.sh` onto a
  loop stick, UEFI boot as USB on an emulated Cortex-A72 (`virt` + AAVMF): GRUB auto-boots,
  autologin, data partition mounted, version stamp `arm64`. Fixed on the way: live-build
  gave the arm64 ISO no partition table (its GPT hybrid option needs syslinux), so
  `build_iso.sh` now appends the EFI image as an ESP with xorriso, like Debian's arm64 ISOs.
- 2026-09-30: 5-second auto-boot timeout in syslinux and GRUB (they waited forever), via
  `LiveOS/config/bootloaders/` overrides.
- 2026-09-30: Updater verifies every finished download against Kiwix's published SHA-256 and
  deletes a corrupt one. Tested locally and against the real Water ZIM. (Prompted by
  hand-checking the five test-set ZIMs on the flashed stick, which all matched.)
- 2026-09-30: `build_iso.sh` drops live-build's cached bootstrap stage when the target arch
  changes (an arm64 build after amd64 silently restored the amd64 base system and failed
  with `Unable to locate package linux-image-arm64`). Finished ISOs can be kept in `dist/`.
- 2026-09-30: First real amd64 build (live-build 20230502) and boot test. `build_usb.sh` run
  on a 6GB loop-device stick, booted in QEMU as USB under BIOS (syslinux) and UEFI (GRUB,
  OVMF): autologin, `lighthouse-mount` active, data partition at `/media/LighthouseData`,
  desktop shortcut, `/etc/lighthouse-release`, Kiwix opens a ZIM from the stick. Found and
  fixed: no live user (`--apt-recommends false` dropped `user-setup`), no terminal/editor/
  gvfs/udisks2/xdg-user-dirs, no Wi-Fi or GPU firmware. `build_usb.sh` accepts loop devices.
- 2026-09-30: `build_iso.sh` checks for `debian-archive-keyring` (debootstrap aborted on Pop
  without it); added to the build guide deps.
- 2026-09-30: `build_iso.sh` refuses Ubuntu's live-build fork (3.0~a57 rejects `--bootloaders`)
  and says how to install Debian's 20230502; build guide documents it. shellcheck clean.
- 2026-09-30: Released v0.2.0 (tagged, pushed with `v0.1.0` on 6e93a17).
- 2026-09-30: `get_readers.sh` marked executable (`setup.sh` option 2 failed with
  "Permission denied" on a fresh clone).
- 2026-09-30: Versioning: root `VERSION` (0.2.0) is the single source of truth, read by
  `updater.py --version`, `setup.sh`, the ISO (volume ID, `/etc/lighthouse-release`) and
  copied to the stick. `CHANGELOG.md` added; a test keeps its top entry equal to `VERSION`.
  Release steps in CONTRIBUTING.md.
- 2026-09-30: `build_usb.sh` hardened: refuses partitions and any disk holding the running
  system (checked via lsblk mountpoints, so LUKS/LVM roots count), demands `yes-wipe` for
  non-removable disks, checks capacity, makes you type the device name. The data partition
  is added with `sfdisk --append` and verified as exactly one new partition (the old
  `fdisk ... || true` + "last lsblk entry" could have formatted the ISO's EFI partition).
  Skips `readers/.downloads`. Docs now match the real `content/ readers/` layout.
  Preflight tested against this machine's disks; sfdisk step tested on a fake hybrid-ISO image.
- 2026-09-30: Cross-building fixed on paper: `auto/config` adds `--bootstrap-qemu-*` when the
  target differs from the host and uses grub-efi only on arm64; `build_iso.sh` validates the
  arch, checks qemu-user-static + binfmt, and clears generated config so one arch's settings
  can't leak into the next build. Build guide deps corrected (`exfat-utils` → `exfatprogs`).
  Still needs a real build (see PENDING).
- 2026-09-30: `get_readers.sh` fetches the latest readers through Kiwix's permalinks
  (was pinned to 2.3.1 / Android 3.9.2, which 404s), keeps versioned downloads so resume
  can't mix releases, records `readers/VERSIONS.txt`, and extracts the Windows zip
  without assuming its folder name. Tested end to end with the Windows reader (2.5.1).
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

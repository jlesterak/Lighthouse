# Lighthouse TODO

Resumed 2026-09-30 after a break since 2026-03-05 (started with Gemini; now Claude Code).
Findings come from an audit of the code on 2026-09-30.

## [PENDING]

Nothing left an agent can do without Jake's hands. Jake's list, in priority order
(checked 2026-10-08):

1. **(you) Publish v0.3.0 on GitHub** (2 min). Pushes the release tag plus the docs/dist
   commits after it:
   `cd ~/Lighthouse && python3 -m unittest discover -s tests && git push origin master && git push origin v0.3.0`
   Look for: the tag on https://github.com/jlesterak/Lighthouse/tags. icebox's mirror picks it up on its own.
2. **(you, sudo) Rebuild the ISOs** so `dist/` holds 0.3.0 (`dist/` still has the 0.2.0 pair).
   `build_iso.sh` now drops `dist/lighthouse-0.3.0-<arch>.iso` + `.sha256` itself:
   `cd ~/Lighthouse && sudo ./build_iso.sh amd64 2>&1 | tee build-amd64.log && sudo ./build_iso.sh arm64 2>&1 | tee build-arm64.log`
   (amd64 ~30-60 min, arm64 ~2 h under qemu-user; can run unattended). Then: `ls dist/ && (cd dist && sha256sum -c *.sha256)`
   and `rm dist/lighthouse-0.2.0-*.iso` once both are OK.
   - 2026-10-09: **arm64 0.3.0 built and `sha256sum -c` OK.** amd64 rebuild still to do (label only); the old
     `lighthouse-0.2.0-arm64.iso` deleted 2026-10-09. Standing rule (Jake): once a newer ISO for the same arch
     passes `sha256sum -c`, delete the superseded one without asking (keep 0.2.0 amd64 until 0.3.0 amd64 exists).
   - arm64 is the one that matters: the 0.2.0 arm64 image predates the Wi-Fi fix and persistence.
   - amd64 only changes the label: the image on the stick (built 2026-10-01 after the Wi-Fi and
     persistence fixes, verified on hardware 2026-10-06) says "Lighthouse 0.2.0 amd64" but nothing in
     `LiveOS/` changed since. **Don't reflash the stick for it**; keep it serving the library on picebox.
3. **(you) Open the LIGHTHOUSE partition on Windows, macOS and Android.** Takes the library offline
   while the stick is away: on picebox first `docker stop kiwix && sudo umount /mnt/lighthouse`, unplug.
   Checklist (the user guide says the same, so this also tests the guide):
   - [ ] Windows: a `LIGHTHOUSE` drive letter appears. Expect possibly one "format this disk?" prompt
         for the ISO area: click Cancel. No prompt for `persistence` (type 83 is hidden).
   - [ ] Windows: `readers\windows\kiwix-desktop.exe` starts (if a VCRUNTIME/MSVCP DLL error:
         run `vc_redist.x64.exe` from that folder) and opens a ZIM from `content\` with search working.
   - [ ] macOS: `LIGHTHOUSE` mounts in Finder and files open; there is no Mac reader on the stick
         (Kiwix is App Store only), so just check the ZIMs are readable/copyable.
   - [ ] Android (OTG): the file manager shows the drive; `readers/kiwix-android.apk` installs; Kiwix opens
         a ZIM straight from the stick. If Kiwix can't see the stick, note which phone/Android version
         (the guide's fallback is copying the ZIM to the phone).
   - [ ] Back on picebox: plug in, `sudo mount /mnt/lighthouse && docker start kiwix`, check http://wiki.home.arpa.
   Tell an agent what failed; it fixes the docs or scripts.
4. **(you, optional) Refresh the stick's top-level files.** The stick was flashed 2026-10-01 10:48, before
   the updater fix for Wikimedia-hosted ZIMs (403 stall, 38bd21c), and its `VERSION` says 0.2.0.
   Only matters if anyone runs `updater.py` from the stick. From pop-os:
   `scp ~/Lighthouse/{updater.py,manifest.json,VERSION} picebox:/tmp/` then on picebox:
   `sudo mount -o remount,rw /mnt/lighthouse && sudo cp /tmp/{updater.py,manifest.json,VERSION} /mnt/lighthouse/ && sudo mount -o remount,ro /mnt/lighthouse`

## [IN PROGRESS]

## [COMPLETED]
- 2026-10-08: arm64 real-hardware test dropped (Jake): no UEFI arm64 machine on hand; build guide now says QEMU-tested only.

- 2026-10-01 notes moved from PENDING: data partition verified on Linux (picebox mounts it,
  kiwix-serve serves the ZIMs); amd64 ISO rebuilt with wpasupplicant + persistence, `build_usb.sh`
  tested 15/15 on a loop device, the 1 TB stick re-flashed with the new layout and its content restored.
  The Wi-Fi re-test passed in boot test 2 (2026-10-06).
- 2026-10-08: Docs audit against the code: user guide (Windows reader path, no Mac reader, persistence,
  failsafe, kiwix-serve, Android OTG fallback), build guide (OS reserve, persistence, `--update-os`,
  `dist/`), architecture (no custom wallpaper), README (wikihow removed from Kiwix), `setup.sh` arm64
  hint (not Apple Silicon/Chromebook/stock Pi), CHANGELOG 0.3.0 links, CONTRIBUTING release steps.
- 2026-10-08: `build_iso.sh` copies each finished ISO to `dist/lighthouse-<version>-<arch>.iso`
  with a `.sha256` (chowned back to the sudo user); the copy step tested on a fake ISO, shellcheck clean.
- 2026-10-06: Boot test 2 passed on real amd64 hardware (Jake): Wi-Fi connects, persistence
  remembers the network across reboot, the failsafe entry boots fresh. Released v0.3.0
  (VERSION, CHANGELOG, local tag). amd64 Wi-Fi/wpasupplicant fix from 2026-10-01 verified.
- 2026-10-06: Temporary sudoers rule `/etc/sudoers.d/lighthouse-temp` is gone (file absent,
  no passwordless sudo).
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

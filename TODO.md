# Lighthouse TODO

Resumed 2026-09-30 after a break since 2026-03-05 (Claude Code).
Findings come from an audit of the code on 2026-09-30.

## [PENDING]
Nothing left an agent can do without Jake's hands. Jake's list, in priority order
(checked 2026-10-08; v0.3.0 publish done, see COMPLETED):

1. **(you; after the Khan build is retried or dropped) Open the LIGHTHOUSE partition on Windows, macOS and Android.** Takes the library offline
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
## [IN PROGRESS]
- [BLOCKED: Jake decides retry or drop] Khan Academy ZIM build on picebox. kolibri2zim 1.1.1 in venv `picebox:~/k2z` (local
  timeout+retry patch in `zimscraperlib/download.py`, original `download.py.orig`), channel c9d7f950ab6b5a1199e3d6c10d7f0103
  (English, US, 68 GB), output to `/mnt/lighthouse/.k2z/out/`. Log `picebox:~/k2z.log` (old: `~/k2z.log.hung-2026-11-07`).
  2026-11-07 first run hung (no-timeout download), patched and restarted 17:37; ran at ~0.36 GB/h.
  2026-11-11 09:43: **failed**: HTTP 404 on one subtitle file (`f6b8d91b2f720c24e768e0959227dd6d.vtt`) from
  studio.learningequality.org; any failed file aborts the run and kolibri2zim removed its build folder, so no partial
  output survives (checked 11-11: `.k2z/out` and `.k2z/tmp` empty, stick mounted ro, kiwix up). A retry needs the patch to
  skip 404s (or drop subtitles) and another ~week of the stick mounted rw. Alternatives already rejected: Kiwix's
  `khanacademy_en_all_2023-03` (180 GB, 2023, no full-text index), Kolibri itself (new service, not Kiwix-readable).
  Cleanup either way: `rm -rf /mnt/lighthouse/.k2z`; if dropped, delete `~/k2z`.
## [COMPLETED]
- 2026-11-07: amd64 0.3.0 ISO built; both 0.3.0 ISOs pass `sha256sum -c`; `lighthouse-0.2.0-amd64.iso` deleted (standing rule).
  The stick is not reflashed: amd64 only changed the label.
- 2026-11-07: Stick top-level files refreshed (updater.py, manifest.json, VERSION 0.3.0); sha256 matches the repo, remounted ro.
- 2026-10-25: NAEB ZIM `naeb_ethnobotany.zim` (34 MB, tools/site2zim.py) on the stick, icebox `~/kit/zim/` and pop-os `content/`; raw mirror purged 2026-10-29.
(Entries before 2026-10-08 archived 2026-10-24; CHANGELOG.md and git history have them.)
- 2026-10-08: v0.3.0 published on GitHub with its tag (checked on origin 2026-10-26).
- 2026-10-20: Relicensed GPL-3.0 → The Unlicense (Jake).
- 2026-10-08: arm64 real-hardware test dropped (Jake): no UEFI arm64 machine on hand; build guide says QEMU-tested only.
- 2026-10-08: Docs audit against the code (user guide, build guide, architecture, README, setup.sh, CHANGELOG, CONTRIBUTING).
- 2026-10-08: `build_iso.sh` copies each finished ISO to `dist/lighthouse-<version>-<arch>.iso` with a `.sha256`.

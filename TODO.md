# Lighthouse TODO

Resumed 2026-09-30 after a break since 2026-03-05 (Claude Code).
Findings come from an audit of the code on 2026-09-30.

## [PENDING]
Nothing left an agent can do without Jake's hands. Jake's list, in priority order
(checked 2026-10-08; v0.3.0 publish done, see COMPLETED):

1. **[IN PROGRESS 2026-11-07, Jake running amd64 build] (you, sudo) Rebuild the ISOs** so `dist/` holds 0.3.0 (`dist/` still has the 0.2.0 pair).
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
2. **(you; not until the Khan build below finishes) Open the LIGHTHOUSE partition on Windows, macOS and Android.** Takes the library offline
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
- [IN PROGRESS] Khan Academy ZIM build on picebox (started 2026-11-07 13:11, Jake approved). kolibri2zim 1.1.1 in venv `picebox:~/k2z`
  (1.2.x needs Python 3.12; the pip build lacks JS assets, so `get_js_deps.sh` from tag v1.1.1 was run into the venv's
  `kolibri2zim/templates/assets`). Channel c9d7f950ab6b5a1199e3d6c10d7f0103 (English, US curriculum, 68 GB published), full,
  no re-encode, with a full-text index. Log `picebox:~/k2z.log`; output `/mnt/lighthouse/.k2z/out/khanacademy_en_us_2026-11.zim`
  (kept out of `content/` so kiwix's `*.zim` glob doesn't pick up a partial file). **The stick stays mounted rw until it's done.**
  When done: mv into `content/`, `rm -rf /mnt/lighthouse/.k2z`, remount ro, `docker restart kiwix`, check search; copy to the icebox kit
  if there's room; delete `~/k2z`. Chose this over Kiwix's `khanacademy_en_all_2023-03` (180 GB, 2023, no full-text index) and Kolibri
  itself (a new service, not readable by Kiwix).
## [COMPLETED]
- 2026-11-07: Stick top-level files refreshed (updater.py, manifest.json, VERSION 0.3.0); sha256 matches the repo, remounted ro.
- 2026-10-25: NAEB ZIM (Native American Ethnobotany, naeb.brit.org): mirrored (49.3k pages), built `naeb_ethnobotany.zim` (34 MB)
  with tools/site2zim.py; on the stick (`content/`, served by picebox kiwix, search checked), icebox `~/kit/zim/`, pop-os `content/`.
  Every page shares one `<title>`, so title suggestions are useless; full-text search works. The raw mirror (576 MB) was purged
  with the 2026-10-24 archive run on 2026-10-29 (gone from `~/_archive/`, checked 2026-10-31); the ZIM is the keeper.
(Entries before 2026-10-08 archived 2026-10-24; CHANGELOG.md and git history have them.)
- 2026-10-08: v0.3.0 published on GitHub with its tag (checked on origin 2026-10-26).
- 2026-10-20: Relicensed GPL-3.0 → The Unlicense (Jake): LICENSE and README updated; sole author, so no consent needed.
- 2026-10-08: arm64 real-hardware test dropped (Jake): no UEFI arm64 machine on hand; build guide now says QEMU-tested only.
- 2026-10-08: Docs audit against the code: user guide (Windows reader path, no Mac reader, persistence,
  failsafe, kiwix-serve, Android OTG fallback), build guide (OS reserve, persistence, `--update-os`,
  `dist/`), architecture (no custom wallpaper), README (wikihow removed from Kiwix), `setup.sh` arm64
  hint (not Apple Silicon/Chromebook/stock Pi), CHANGELOG 0.3.0 links, CONTRIBUTING release steps.
- 2026-10-08: `build_iso.sh` copies each finished ISO to `dist/lighthouse-<version>-<arch>.iso`
  with a `.sha256` (chowned back to the sudo user); the copy step tested on a fake ISO, shellcheck clean.

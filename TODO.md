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
- [BLOCKED: Jake decides on another retry] Khan Academy ZIM build on picebox, retry approved 2026-11-11 and run; failed again 2026-11-13. kolibri2zim 1.1.1 in
  venv `picebox:~/k2z`, channel c9d7f950ab6b5a1199e3d6c10d7f0103 (English, US, 68 GB), output `/mnt/lighthouse/.k2z/out/`.
  Local patches (originals kept as `*.orig` next to each file; full diff in `tools/kolibri2zim-1.1.1-lighthouse.patch`):
  `zimscraperlib/download.py` timeout+retry (11-07 hang fix); `kolibri2zim/debug.py` + `scraper.py` (11-11): HTTP 404/410
  is not retried, the file is logged `PATCH skip file ...` and left out (a gone subtitle is also dropped from the player;
  a gone exercise/HTML5 archive skips that node, `PATCH skip ... node`). Other errors still fail the run as before.
  History: 11-07 first run hung (no timeout); 11-07 17:37 restart ran ~4 days at ~0.36 GB/h, then 11-11 09:43 died on one
  404 subtitle (`f6b8d91b2f720c24e768e0959227dd6d.vtt`) and kolibri2zim deleted its build folder (no partial output).
  **2026-11-11 18:46 retry (patched) ran ~51 h:** 2,822 gone files skipped as designed, then 2026-11-13 21:35 it died on
  "Network is unreachable" (5 retries exhausted on one `.vtt`; not a 404, so the patch does not skip it) and again deleted its build
  folder; `.k2z/out/` is empty and the stick is ro again (checked 2026-11-16). A WAN drop of a few minutes kills a week-long run.
  **Next (Jake decides):** drop it, or retry once the downloader waits out network errors (needs a patch change first). Retry steps: Jake: `ssh -t picebox sudo mount -o remount,rw /mnt/lighthouse` (fstab mounts it ro; no sudo-free way). Then
  `ssh picebox ~/k2z-start.sh` (checks rw, cleans `.k2z`, moves `~/k2z.log` aside with a date suffix, starts kolibri2zim
  detached with setsid). Expect ~a week with the stick rw. Not resumable mid-run: a restart starts over.
  Monitor: `ssh picebox 'pgrep -af bin/kolibri2zim; echo age=$(( $(date +%s) - $(stat -c %Y ~/k2z.log) ))s; grep -c download_to ~/k2z.log; grep -c "PATCH skip" ~/k2z.log; grep -cE "ERROR|Interrupting|FAILURE" ~/k2z.log; ls -la /mnt/lighthouse/.k2z/out/'`.
  Alternatives already rejected: Kiwix's `khanacademy_en_all_2023-03` (180 GB, 2023, no full-text index), Kolibri itself.
  When done: ZIM into `content/`, remount ro, `rm -rf /mnt/lighthouse/.k2z`. If dropped: also delete `~/k2z` and `~/k2z-start.sh`.
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

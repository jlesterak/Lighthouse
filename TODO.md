# Lighthouse TODO

Resumed 2026-09-30 after a break since 2026-03-05 (Claude Code).
Findings come from an audit of the code on 2026-09-30.

## [PENDING]

Nothing left an agent can do without Jake's hands. Jake's list, in priority order
(checked 2026-10-08):

1. **[DONE 2026-10-08: v0.3.0 pushed with its tag]** ~~Publish v0.3.0 on GitHub~~ (2 min). Pushes the release tag plus the docs/dist
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
- **NAEB ZIM** [PAUSED] (Jake, 2026-10-09): Native American Ethnobotany DB (http://naeb.brit.org, BRIT; HTTP only, no robots.txt;
  ~44.7k use records + ~4.4k species + tribes, ~50k pages of ~4-12 KB). PAUSED (Jake 2026-10-09: offline for a while; ~1k pages done, a rerun starts over). Mirror in
  the local naeb-mirror copy (archived 2026-10-24; restore it before resuming; `run.sh`, wget, 0.25 s random wait, ~4-5 h; rerun to resume, log `wget.log`, ends with `DONE`).
  Then: `tools/site2zim.py <naeb-mirror>/naeb.brit.org --name naeb_ethnobotany --title "Native American Ethnobotany"
  --main index.html --title-sep " - "` (check a page title first), open it in kiwix-serve, then onto the stick +
  icebox:~/kit next to the LEMON ZIM.

## [COMPLETED]
(Entries before 2026-10-08 archived 2026-10-24; CHANGELOG.md and git history have them.)
- 2026-10-20: Relicensed GPL-3.0 → The Unlicense (Jake): LICENSE and README updated; sole author, so no consent needed.
- 2026-10-08: arm64 real-hardware test dropped (Jake): no UEFI arm64 machine on hand; build guide now says QEMU-tested only.
- 2026-10-08: Docs audit against the code: user guide (Windows reader path, no Mac reader, persistence,
  failsafe, kiwix-serve, Android OTG fallback), build guide (OS reserve, persistence, `--update-os`,
  `dist/`), architecture (no custom wallpaper), README (wikihow removed from Kiwix), `setup.sh` arm64
  hint (not Apple Silicon/Chromebook/stock Pi), CHANGELOG 0.3.0 links, CONTRIBUTING release steps.
- 2026-10-08: `build_iso.sh` copies each finished ISO to `dist/lighthouse-<version>-<arch>.iso`
  with a `.sha256` (chowned back to the sudo user); the copy step tested on a fake ISO, shellcheck clean.

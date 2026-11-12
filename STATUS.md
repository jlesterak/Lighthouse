# Status (2026-11-11)
2026-11-11: Khan ZIM retry approved: kolibri2zim patched to skip HTTP 404/410 files (`tools/kolibri2zim-1.1.1-lighthouse.patch`, tested on the 404 that killed the 11-07 run) and launcher `picebox:~/k2z-start.sh` ready. **Blocked on Jake:** the stick is ro and the rw remount needs sudo (TODO.md). Then ~a week of build.
2026-11-07: `dist/` holds only the 0.3.0 amd64 and arm64 ISOs (checksums OK); stick files refreshed to 0.3.0.
Released v0.3.0 (tag on GitHub since 2026-10-08). Unlicense since 2026-10-20. NAEB ethnobotany ZIM on the stick, icebox kit and pop-os `content/` (2026-10-25).
`master` is 8 docs commits ahead of GitHub (checked 2026-11-11; push needs Jake's OK). Disk: dist 2.2 GB, content 0.8 GB, readers 0.9 GB, plus root-owned live-build output.

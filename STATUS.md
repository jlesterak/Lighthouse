# Status (2026-11-16)
2026-11-13: Khan ZIM retry (patched kolibri2zim, started 11-11 18:46) failed after ~51 h on a network-unreachable error and deleted its build folder; no output. 2026-11-16: Jake decided the build must survive network drops; the downloader now waits out outages up to 24 h per file (tested on picebox). Retry waits on Jake's rw remount of the stick (`TODO.md`).
2026-11-07: `dist/` holds only the 0.3.0 amd64 and arm64 ISOs (checksums OK); stick files refreshed to 0.3.0.
Released v0.3.0 (tag on GitHub since 2026-10-08). Unlicense since 2026-10-20. NAEB ethnobotany ZIM on the stick, icebox kit and pop-os `content/` (2026-10-25).
`master` matches GitHub (e167b2a, checked 2026-11-16). Disk: dist 2.2 GB, content 0.8 GB, readers 0.9 GB, plus root-owned live-build output.

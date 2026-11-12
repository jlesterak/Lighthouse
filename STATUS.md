# Status (2026-11-11)
2026-11-11: the Khan ZIM build **failed** at 09:43 after ~4 days: one subtitle file (.vtt) returned HTTP 404 from studio.learningequality.org, kolibri2zim aborts on any failed file and deleted its build folder (nothing kept; `.k2z/out` empty). Stick now mounted ro. Retry or drop is Jake's call (TODO.md).
2026-11-07: `dist/` holds only the 0.3.0 amd64 and arm64 ISOs (checksums OK); stick files refreshed to 0.3.0.
Released v0.3.0 (tag on GitHub since 2026-10-08). Unlicense since 2026-10-20. NAEB ethnobotany ZIM on the stick, icebox kit and pop-os `content/` (2026-10-25).
`master` is 8 docs commits ahead of GitHub (checked 2026-11-11; push needs Jake's OK). Disk: dist 2.2 GB, content 0.8 GB, readers 0.9 GB, plus root-owned live-build output.

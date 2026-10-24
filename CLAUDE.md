# Lighthouse (offline knowledge USB / ISO)

Global rules in `~/.claude/CLAUDE.md` apply. Public GitHub repo (`origin`; push needs Jake's approval). Unlicense. No secrets or private hostnames in commits.

- Builds a bootable live USB/ISO with offline knowledge (ZIM files and readers). Scripts: `setup.sh`, `build_iso.sh`, `build_usb.sh`, `get_readers.sh`; `updater.py` refreshes content from `manifest.json`; `VERSION` drives the release.
- Big state is gitignored and regenerable: `content/`, `readers/`, `dist/` (finished ISOs), `LiveOS/{cache,chroot,binary}` (root-owned live-build output, ~11 GB total). Cleaning `LiveOS` needs sudo, so ask first.
- The stick is also Jake's offline kit: `~/kit` and `~/homelab/kit/` feed it. Local plaintext secrets there are intentional.
- `TODO.md` is the only todo list; `STATUS.md` is the summary. Releases (tags, GitHub) need Jake's approval.
- Related: NAEB database -> ZIM work is tracked in `TODO.md`; the mirror is `~/naeb-mirror`.

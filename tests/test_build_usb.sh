#!/bin/bash
# End-to-end test of build_usb.sh on a loop device (an image file, never a real disk).
# Needs root and a built ISO:   sudo tests/test_build_usb.sh [amd64|arm64]
# Checks: data partition starts at the OS reserve, persistence file is a valid ext4 image
# with persistence.conf, and --update-os keeps the LIGHTHOUSE partition and its files.
set -uo pipefail
cd "$(dirname "$0")/.." || exit 1
[ "$(id -u)" = 0 ] || { echo "run with sudo"; exit 1; }
ARCH=${1:-amd64}
[ -f "LiveOS/live-image-${ARCH}.hybrid.iso" ] || { echo "no LiveOS/live-image-${ARCH}.hybrid.iso: build it first"; exit 1; }

LOGS=$(mktemp -d -p "${TMPDIR:-/var/tmp}" lighthouse-test-logs-XXXX)
IMG=$(mktemp -p "${TMPDIR:-/var/tmp}" lighthouse-test-XXXX.img)
truncate -s 12G "$IMG"
LOOP=$(losetup -fP --show "$IMG")
M=$(mktemp -d); P=$(mktemp -d)
cleanup(){ umount "$P" "$M" 2>/dev/null; rmdir "$P" "$M" 2>/dev/null; losetup -d "$LOOP" 2>/dev/null; rm -f "$IMG"; }
trap cleanup EXIT

pass=0; fail=0
check(){ if eval "$2"; then echo "  PASS $1"; pass=$((pass+1)); else echo "  FAIL $1"; fail=$((fail+1)); fi; }

echo "## fresh build on $LOOP"
# answers: the not-USB 'yes-wipe' confirmation, then the device name
printf 'yes-wipe\n%s\n' "$LOOP" | PERSIST_GIB=1 ./build_usb.sh "$LOOP" "$ARCH" > "$LOGS/build.log" 2>&1
rc=$?
check "build exits 0" "[ $rc = 0 ]"
partprobe "$LOOP"; udevadm settle
DATA=$(lsblk -nro NAME,LABEL "$LOOP" | awk '$2=="LIGHTHOUSE"{print "/dev/"$1}')
check "LIGHTHOUSE partition exists" "[ -n '$DATA' ]"
START=$(cat "/sys/class/block/$(basename "$DATA")/start" 2>/dev/null || echo 0)
check "data starts at the 4 GiB reserve" "[ $START = $(( 4 * 1073741824 / 512 )) ]"
mount "$DATA" "$M"
check "persistence file is 1 GiB" "[ \$(stat -c %s '$M/persistence') = 1073741824 ]"
mount -o loop,ro "$M/persistence" "$P"
check "persistence is ext4 with persistence.conf '/ union'" "[ \"\$(cat '$P/persistence.conf')\" = '/ union' ]"
umount "$P"
echo marker > "$M/marker.txt"; sync; umount "$M"

echo "## --update-os keeps the data"
printf '%s\n' "$LOOP" | ./build_usb.sh --update-os "$LOOP" "$ARCH" > "$LOGS/update.log" 2>&1
rc=$?
check "update exits 0" "[ $rc = 0 ]"
partprobe "$LOOP"; udevadm settle
DATA2=$(lsblk -nro NAME,LABEL "$LOOP" | awk '$2=="LIGHTHOUSE"{print "/dev/"$1}')
START2=$(cat "/sys/class/block/$(basename "$DATA2")/start" 2>/dev/null || echo 0)
check "LIGHTHOUSE back at the same start" "[ $START2 = $START ]"
mount "$DATA2" "$M"
check "marker file survived" "[ \"\$(cat '$M/marker.txt')\" = marker ]"
check "persistence file survived" "[ -f '$M/persistence' ]"
umount "$M"
check "ISO partition readable again" "lsblk -nro FSTYPE '$LOOP' | grep -q iso9660"

echo "## --update-os refuses an ISO bigger than the OS space (the pre-reserve layout case)"
BIG=$(mktemp -p "${TMPDIR:-/var/tmp}" lighthouse-big-XXXX.iso)
truncate -s $(( START * 512 + 1 )) "$BIG"          # sparse: huge on paper, no disk used
printf '%s\n' "$LOOP" | ISO_FILE="$BIG" ./build_usb.sh --update-os "$LOOP" "$ARCH" > "$LOGS/toobig.log" 2>&1
rc=$?; rm -f "$BIG"
check "oversized ISO refused before writing" "[ $rc = 1 ] && grep -q 'would destroy the start of your data' '$LOGS/toobig.log'"
mount "$DATA2" "$M"; check "marker still there after refusal" "[ -f '$M/marker.txt' ]"; umount "$M"

echo "== $pass passed, $fail failed (logs: $LOGS)"
[ "$fail" = 0 ]

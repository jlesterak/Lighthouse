#!/bin/bash
# End-to-end test of build_usb.sh on a loop device (an image file, never a real disk).
# Needs root and a built ISO:   sudo tests/test_build_usb.sh [amd64|arm64]
# Checks: persistence partition at the OS reserve (ext4, label persistence, persistence.conf),
# data right after it, and --update-os keeps both partitions and their files.
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
cleanup(){ umount "$P" "$M" 2>/dev/null; rmdir "$P" "$M" 2>/dev/null; losetup -d "$LOOP" 2>/dev/null; rm -f "$IMG"; chmod -R a+rX "$LOGS"; }
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
PERS=$(lsblk -nro NAME,LABEL "$LOOP" | awk '$2=="persistence"{print "/dev/"$1}')
PSTART=$(cat "/sys/class/block/$(basename "$PERS")/start" 2>/dev/null || echo 0)
START=$(cat "/sys/class/block/$(basename "$DATA")/start" 2>/dev/null || echo 0)
check "persistence partition starts at the 4 GiB reserve" "[ $PSTART = $(( 4 * 1073741824 / 512 )) ]"
check "persistence is ext4, type 83" "[ \"\$(lsblk -nro FSTYPE '$PERS')\" = ext4 ] && sfdisk -d '$LOOP' | grep '^$PERS ' | grep -q 'type=83'"
check "data starts right after 1 GiB of persistence" "[ $START = $(( 5 * 1073741824 / 512 )) ]"
mount "$PERS" "$P"
check "persistence.conf is '/ union'" "[ \"\$(cat '$P/persistence.conf')\" = '/ union' ]"
echo pmarker > "$P/pmarker.txt"; sync; umount "$P"
mount "$DATA" "$M"
echo marker > "$M/marker.txt"; sync; umount "$M"

echo "## --update-os keeps the data"
printf 'yes-wipe\n%s\n' "$LOOP" | ./build_usb.sh --update-os "$LOOP" "$ARCH" > "$LOGS/update.log" 2>&1
rc=$?
check "update exits 0" "[ $rc = 0 ]"
check "update actually wrote the ISO" "grep -q 'OS updated' '$LOGS/update.log'"
partprobe "$LOOP"; udevadm settle
DATA2=$(lsblk -nro NAME,LABEL "$LOOP" | awk '$2=="LIGHTHOUSE"{print "/dev/"$1}')
START2=$(cat "/sys/class/block/$(basename "$DATA2")/start" 2>/dev/null || echo 0)
check "LIGHTHOUSE back at the same start" "[ $START2 = $START ]"
PERS2=$(lsblk -nro NAME,LABEL "$LOOP" | awk '$2=="persistence"{print "/dev/"$1}')
PSTART2=$(cat "/sys/class/block/$(basename "$PERS2")/start" 2>/dev/null || echo 0)
check "persistence back at the same start" "[ $PSTART2 = $PSTART ]"
mount "$DATA2" "$M"
check "data marker survived" "[ \"\$(cat '$M/marker.txt')\" = marker ]"
umount "$M"
mount "$PERS2" "$P"
check "persistence marker survived" "[ \"\$(cat '$P/pmarker.txt')\" = pmarker ]"
umount "$P"
check "ISO partition readable again" "lsblk -nro FSTYPE '$LOOP' | grep -q iso9660"

echo "## --update-os refuses an ISO bigger than the OS space (the pre-reserve layout case)"
BIG=$(mktemp -p "${TMPDIR:-/var/tmp}" lighthouse-big-XXXX.iso)
truncate -s $(( PSTART * 512 + 1 )) "$BIG"          # sparse: huge on paper, no disk used
printf 'yes-wipe\n%s\n' "$LOOP" | ISO_FILE="$BIG" ./build_usb.sh --update-os "$LOOP" "$ARCH" > "$LOGS/toobig.log" 2>&1
rc=$?; rm -f "$BIG"
check "oversized ISO refused before writing" "[ $rc = 1 ] && grep -q 'would destroy the start of your data' '$LOGS/toobig.log'"
mount "$DATA2" "$M"; check "marker still there after refusal" "[ -f '$M/marker.txt' ]"; umount "$M"

echo "== $pass passed, $fail failed (logs: $LOGS)"
[ "$fail" = 0 ]

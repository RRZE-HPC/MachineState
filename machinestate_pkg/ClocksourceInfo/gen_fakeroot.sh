#!/usr/bin/env bash
set -euo pipefail

SRC="/sys/devices/system/clocksource"
BASE="./tests"

FULL="$BASE/full/sys/devices/system/clocksource"
EXT="$BASE/extended/sys/devices/system/clocksource"
MISS="$BASE/missing_current/sys/devices/system/clocksource"

echo "Rebuilding fake root under $BASE ..."
rm -rf "$BASE/full" "$BASE/extended" "$BASE/missing_current"

mkdir -p "$FULL" "$EXT" "$MISS"

copy_fixture_tree() {
    local dst_root="$1"
    local copy_available="$2"

    for srcdir in "$SRC"/clocksource*; do
        [ -d "$srcdir" ] || continue
        name="$(basename "$srcdir")"
        dstdir="$dst_root/$name"
        mkdir -p "$dstdir"

        if [ -f "$srcdir/current_clocksource" ]; then
            cp "$srcdir/current_clocksource" "$dstdir/current_clocksource"
        fi

        if [ "$copy_available" = "yes" ] && [ -f "$srcdir/available_clocksource" ]; then
            cp "$srcdir/available_clocksource" "$dstdir/available_clocksource"
        fi
    done
}

# full: only current_clocksource
copy_fixture_tree "$FULL" "no"

# extended: current_clocksource + available_clocksource
copy_fixture_tree "$EXT" "yes"

# missing_current: same as full first
copy_fixture_tree "$MISS" "no"

# remove one current_clocksource file to simulate missing required file
first_current="$(find "$MISS" -type f -name current_clocksource | sort | head -n 1 || true)"
if [ -n "${first_current:-}" ]; then
    rm -f "$first_current"
    echo "Removed $first_current for missing_current fixture"
fi

# create empty output placeholders if they do not exist
: > "$BASE/full/output"
: > "$BASE/extended/output"
: > "$BASE/missing_current/output"

echo "Done."
echo
echo "Created:"
echo "  $BASE/full"
echo "  $BASE/extended"
echo "  $BASE/missing_current"
#!/usr/bin/env bash
# The C checks, in the style of regulae's scripts/check.sh.
#
#   scripts/check.sh            gcc and clang builds with -Werror, ctest each
#   scripts/check.sh --full     also ASan and UBSan builds (ctest each), and
#                               every libFuzzer target for AP_FUZZ_SECONDS (15)
#
# Build trees go under ${AP_CHECK_DIR:-build/check} and are removed at the end
# unless AP_KEEP_BUILDS=1. merkmal is taken from ${AP_MERKMAL_SOURCE_DIR:-../merkmal}.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DIR="${AP_CHECK_DIR:-$ROOT/build/check}"
MERKMAL="${AP_MERKMAL_SOURCE_DIR:-$ROOT/../merkmal}"
SECONDS_PER_FUZZER="${AP_FUZZ_SECONDS:-15}"
JOBS="${AP_JOBS:-4}"
FULL=0
[[ "${1:-}" == "--full" ]] && FULL=1

build_and_test() {
    local name="$1"; shift
    echo "== $name"
    cmake -S "$ROOT" -B "$DIR/$name" -DAP_WERROR=ON -DAP_MERKMAL_SOURCE_DIR="$MERKMAL" "$@" > "$DIR/$name.configure.log"
    cmake --build "$DIR/$name" -j "$JOBS" > "$DIR/$name.build.log" 2>&1 || { tail -40 "$DIR/$name.build.log"; exit 1; }
    (cd "$DIR/$name" && ctest --output-on-failure) | tail -3
}

mkdir -p "$DIR"
build_and_test gcc -DCMAKE_C_COMPILER=gcc -DCMAKE_BUILD_TYPE=Release
build_and_test clang -DCMAKE_C_COMPILER=clang -DCMAKE_BUILD_TYPE=Release
if [[ $FULL == 1 ]]; then
    # gcc: this repository's sanitizer runtimes are gcc's (clang's may be absent)
    build_and_test asan -DCMAKE_C_COMPILER=gcc -DCMAKE_BUILD_TYPE=Debug -DAP_ENABLE_SANITIZER=address
    build_and_test ubsan -DCMAKE_C_COMPILER=gcc -DCMAKE_BUILD_TYPE=Debug -DAP_ENABLE_SANITIZER=undefined
    echo "== fuzz (${SECONDS_PER_FUZZER}s each)"
    cmake -S "$ROOT" -B "$DIR/fuzz" -DCMAKE_C_COMPILER=clang -DCMAKE_BUILD_TYPE=Debug \
        -DAP_BUILD_FUZZERS=ON -DAP_BUILD_TESTS=OFF -DAP_BUILD_TOOLS=OFF \
        -DAP_MERKMAL_SOURCE_DIR="$MERKMAL" > "$DIR/fuzz.configure.log"
    cmake --build "$DIR/fuzz" -j "$JOBS" > "$DIR/fuzz.build.log" 2>&1 || { tail -40 "$DIR/fuzz.build.log"; exit 1; }
    for t in parse_rule parse_sequence apply model_load; do
        mkdir -p "$DIR/fuzz/corpus_$t"
        "$DIR/fuzz/fuzz_$t" -max_total_time="$SECONDS_PER_FUZZER" -max_len=512 \
            "$DIR/fuzz/corpus_$t" "$ROOT/fuzz/corpus" > "$DIR/fuzz_$t.log" 2>&1 \
            || { tail -60 "$DIR/fuzz_$t.log"; exit 1; }
        echo "   fuzz_$t: $(grep -Eo '#[0-9]+[[:space:]]+DONE.*' "$DIR/fuzz_$t.log" | head -1)"
    done
fi
[[ "${AP_KEEP_BUILDS:-0}" == 1 ]] || rm -rf "$DIR"
echo "all checks passed"

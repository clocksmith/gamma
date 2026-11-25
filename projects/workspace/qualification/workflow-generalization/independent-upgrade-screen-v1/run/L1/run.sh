#!/usr/bin/env bash
# L1 (OpenProject 17.7.0 -> 17.8.0): three repeats, each on a fresh pair of instances, then the result file.
#
#   SCREEN_OUT_DIR=<scratch dir> SCREEN_HOLD_FILE=<hold marker> ./run.sh
#
# Uses ../../../screening/openproject-up.sh (a byte-identical copy of the frozen bring-up that mounts the
# screening seeder, which the sealed list names for this pair) and the frozen openproject-down.sh, unchanged. After each down it
# removes only the anonymous volumes that were mounted in this repeat's own containers.
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BRINGUP="$HERE/../../../bringup"
SCREENING="$HERE/../../../screening"
OLD_TAG=17.7.0-slim
NEW_TAG=17.8.0-slim
: "${SCREEN_OUT_DIR:?set SCREEN_OUT_DIR}"
mkdir -p "$SCREEN_OUT_DIR"
CONTAINERS="gammatron-op-old gammatron-op-new gammatron-op-pg15"

hold_wait() { while [ -n "${SCREEN_HOLD_FILE:-}" ] && [ -e "$SCREEN_HOLD_FILE" ]; do sleep 30; done; }

down() { # remove the containers, then the anonymous volumes they had mounted
  local vols
  vols="$(docker inspect $CONTAINERS --format '{{range .Mounts}}{{if eq .Type "volume"}}{{.Name}} {{end}}{{end}}' 2>/dev/null | tr ' ' '\n' | grep -E '^[0-9a-f]{64}$' || true)"
  "$BRINGUP/openproject-down.sh"
  for v in $vols; do docker volume inspect "$v" >/dev/null 2>&1 && docker volume rm "$v" >/dev/null && echo "removed leftover volume ${v:0:12}"; done
  return 0
}

for r in ${REPEATS:-1 2 3}; do
  attempt=1
  while :; do
    hold_wait
    echo "== L1 repeat $r attempt $attempt: bring-up at $(date -u +%Y-%m-%dT%H:%M:%SZ)"
    if ! "$SCREENING/openproject-up.sh" "$OLD_TAG" "$NEW_TAG" >"$SCREEN_OUT_DIR/up-$r-$attempt.log" 2>&1; then
      echo "bring-up failed, see up-$r-$attempt.log"; down
    else
      rm -f "$SCREEN_OUT_DIR/repeat-$r.json"
      PYTHONDONTWRITEBYTECODE=1 python3 "$HERE/run_case.py" "$r"
      down
      if [ -n "${SCREEN_HOLD_FILE:-}" ] && [ -e "$SCREEN_HOLD_FILE" ] || grep -q '"overlapped_hold": true' "$SCREEN_OUT_DIR/repeat-$r.json" 2>/dev/null; then
        echo "repeat $r attempt $attempt overlapped a hold: void, repeating on a fresh instance"
        mv "$SCREEN_OUT_DIR/repeat-$r.json" "$SCREEN_OUT_DIR/void-repeat-$r-attempt-$attempt.json" 2>/dev/null
      elif [ -s "$SCREEN_OUT_DIR/repeat-$r.json" ]; then
        break
      fi
    fi
    attempt=$((attempt + 1))
    [ "$attempt" -gt 3 ] && { echo "repeat $r: gave up after 3 attempts"; break; }
  done
done
PYTHONDONTWRITEBYTECODE=1 python3 "$HERE/assemble.py"

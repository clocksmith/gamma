#!/usr/bin/env bash
# Remove the containers, network and state file that ./openproject-up.sh created.
set -uo pipefail
STATE_DIR="${GAMMATRON_QUAL_STATE:-$HOME/.local/state/gammatron-qual}"
docker rm -f gammatron-op-old gammatron-op-new gammatron-op-pg15 >/dev/null 2>&1
docker network rm gammatron-op-qual-net >/dev/null 2>&1
rm -f "$STATE_DIR/openproject.json" "$STATE_DIR"/gammatron-op-*.log "$STATE_DIR"/gammatron-op-*.env
left="$(docker ps -a --format '{{.Names}}' | grep -c '^gammatron-op-' || true)"
echo "OpenProject qualification containers left: $left"

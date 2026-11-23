#!/usr/bin/env bash
# Remove the containers, network and state file that ./erpnext-up.sh created.
set -uo pipefail
STATE_DIR="${GAMMATRON_QUAL_STATE:-$HOME/.local/state/gammatron-qual}"
docker rm -f gammatron-erp-old gammatron-erp-new gammatron-erp-mariadb gammatron-erp-redis >/dev/null 2>&1
docker network rm gammatron-erp-net >/dev/null 2>&1
rm -f "$STATE_DIR/erpnext.json" "$STATE_DIR"/gammatron-erp-*.log
left="$(docker ps -a --format '{{.Names}}' | grep -c '^gammatron-erp-' || true)"
echo "ERPNext qualification containers left: $left"

#!/usr/bin/env bash
# Bring up two isolated ERPNext releases against one MariaDB 10.6 and one Redis
# container and seed the Stage2 qualification data (clocksmith/deco#88). Costs
# nothing: no model call. Site creation takes several minutes per release.
#
#   ./erpnext-up.sh                    # v15.10.0 on :28510, v15.20.0 on :28520
#   ./erpnext-up.sh v15.20.0 v15.30.0  # any two tags; the same two ports are reused
#
# Everything binds to 127.0.0.1. Passwords are generated on each run and written,
# with the API keys the seeder prints, to a state file outside the repository
# (mode 600). Remove everything with ./erpnext-down.sh.
set -euo pipefail

OLD_TAG="${1:-v15.10.0}"
NEW_TAG="${2:-v15.20.0}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STATE_DIR="${GAMMATRON_QUAL_STATE:-$HOME/.local/state/gammatron-qual}"
STATE_FILE="$STATE_DIR/erpnext.json"
NET=gammatron-erp-net
DB=gammatron-erp-mariadb
REDIS=gammatron-erp-redis
OLD_NAME=gammatron-erp-old
NEW_NAME=gammatron-erp-new
OLD_PORT=28510
NEW_PORT=28520
PLATFORM=linux/amd64
READY_TIMEOUT_S="${READY_TIMEOUT_S:-240}"

command -v docker >/dev/null || { echo "docker not found" >&2; exit 1; }
docker info >/dev/null 2>&1 || { echo "docker daemon not reachable" >&2; exit 1; }
if docker ps -a --format '{{.Names}}' | grep -Eq "^($DB|$REDIS|$OLD_NAME|$NEW_NAME)$"; then
  echo "Containers from an earlier bring-up exist. Run ./erpnext-down.sh first." >&2
  exit 1
fi

rand() { openssl rand -hex "$1"; }
DB_ROOT_PASSWORD="$(rand 16)"
USER_PASSWORD="Aa1!$(rand 12)"

umask 077
mkdir -p "$STATE_DIR"

docker network inspect "$NET" >/dev/null 2>&1 || docker network create "$NET" >/dev/null
docker run -d --platform "$PLATFORM" --name "$DB" --network "$NET" \
  -e MARIADB_ROOT_PASSWORD="$DB_ROOT_PASSWORD" mariadb:10.6 \
  --character-set-server=utf8mb4 --collation-server=utf8mb4_unicode_ci \
  --skip-character-set-client-handshake >/dev/null
docker run -d --platform "$PLATFORM" --name "$REDIS" --network "$NET" redis:6.2-alpine >/dev/null
for _ in $(seq 1 60); do
  docker exec "$DB" mariadb -uroot -p"$DB_ROOT_PASSWORD" -e 'SELECT 1' >/dev/null 2>&1 && break
  sleep 1
done

start_release() { # <container> <tag> <site> <db name> <redis base index> <host port>
  local name="$1" tag="$2" site="$3" dbname="$4" r="$5" port="$6"
  echo "[$name] creating site $site on frappe/erpnext:$tag"
  docker run -d --platform "$PLATFORM" --name "$name" --network "$NET" \
    -p "127.0.0.1:$port:8000" -e "STAGE2_USER_PASSWORD=$USER_PASSWORD" \
    "frappe/erpnext:$tag" sleep infinity >/dev/null
  docker exec "$name" bash -lc "
cat > sites/common_site_config.json <<JSON
{\"db_host\":\"$DB\",\"db_port\":3306,\"redis_cache\":\"redis://$REDIS:6379/$r\",\"redis_queue\":\"redis://$REDIS:6379/$((r + 1))\",\"redis_socketio\":\"redis://$REDIS:6379/$((r + 2))\",\"serve_default_site\":true,\"default_site\":\"$site\"}
JSON
bench new-site $site --force --no-mariadb-socket --db-name $dbname --db-password '$DB_ROOT_PASSWORD' \
  --db-host $DB --db-port 3306 --mariadb-root-password '$DB_ROOT_PASSWORD' \
  --admin-password '$USER_PASSWORD' --install-app erpnext --set-default
nohup bench --site $site serve --port 8000 --noreload > /tmp/bench_serve.log 2>&1 &
" >"$STATE_DIR/$name-site.log" 2>&1
}

seed_release() { # <container> <site> <host port> -> prints the seeder's JSON
  local name="$1" site="$2" port="$3" waited=0
  until curl -sf -o /dev/null "http://127.0.0.1:$port/api/method/ping"; do
    waited=$((waited + 2))
    [ "$waited" -ge "$READY_TIMEOUT_S" ] && { echo "[$name] not ready after ${READY_TIMEOUT_S}s" >&2; return 1; }
    sleep 2
  done
  docker cp "$HERE/seed_erpnext_qual.py" "$name:/tmp/seed_erpnext_qual.py" >/dev/null
  docker exec -w /home/frappe/frappe-bench/sites "$name" ../env/bin/python /tmp/seed_erpnext_qual.py "$site" \
    2>"$STATE_DIR/$name-seed.log" | sed -n 's/^ERP_SEED_JSON://p'
}

start_release "$OLD_NAME" "$OLD_TAG" erp-old.local erp_old_qual 0 "$OLD_PORT"
start_release "$NEW_NAME" "$NEW_TAG" erp-new.local erp_new_qual 3 "$NEW_PORT"
OLD_SEED="$(seed_release "$OLD_NAME" erp-old.local "$OLD_PORT")"
NEW_SEED="$(seed_release "$NEW_NAME" erp-new.local "$NEW_PORT")"
[ -n "$OLD_SEED" ] && [ -n "$NEW_SEED" ] || { echo "seeding printed no result; see $STATE_DIR/*-seed.log" >&2; exit 1; }

OLD_DIGEST="$(docker inspect --format '{{index .RepoDigests 0}}' "frappe/erpnext:$OLD_TAG" 2>/dev/null || true)"
NEW_DIGEST="$(docker inspect --format '{{index .RepoDigests 0}}' "frappe/erpnext:$NEW_TAG" 2>/dev/null || true)"

OLD_SEED="$OLD_SEED" NEW_SEED="$NEW_SEED" python3 - "$STATE_FILE" <<PY
import json, os, sys
state = {
    "schema": "gammatron-qual-erpnext-state/v1",
    "username": "stage2_approver@isolated.local",
    "authorUsername": "stage2_author@isolated.local",
    "password": "$USER_PASSWORD",
    "mariadbContainer": "$DB",
    "mariadbRootPassword": "$DB_ROOT_PASSWORD",
    "old": {"tag": "$OLD_TAG", "image": "$OLD_DIGEST", "container": "$OLD_NAME",
            "url": "http://127.0.0.1:$OLD_PORT", "database": "erp_old_qual",
            "seed": json.loads(os.environ["OLD_SEED"])},
    "new": {"tag": "$NEW_TAG", "image": "$NEW_DIGEST", "container": "$NEW_NAME",
            "url": "http://127.0.0.1:$NEW_PORT", "database": "erp_new_qual",
            "seed": json.loads(os.environ["NEW_SEED"])},
}
with open(sys.argv[1], "w") as f:
    json.dump(state, f, indent=2)
PY
chmod 600 "$STATE_FILE"
echo "ERPNext $OLD_TAG on :$OLD_PORT and $NEW_TAG on :$NEW_PORT are seeded."
echo "State (API keys, passwords): $STATE_FILE"

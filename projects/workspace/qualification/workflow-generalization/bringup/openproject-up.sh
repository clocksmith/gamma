#!/usr/bin/env bash
# Bring up two isolated OpenProject releases against one PostgreSQL 15 container and
# seed the Stage2 qualification data (clocksmith/deco#88). Costs nothing: no model call.
#
#   ./openproject-up.sh                         # 13.4.0-slim on :28413, 14.0.0-slim on :28414
#   ./openproject-up.sh 14.0.0-slim 15.0.0-slim # any two tags; the same two ports are reused
#
# Everything binds to 127.0.0.1. Passwords and keys are generated on each run and
# written, with the API tokens the seeder prints, to a state file outside the
# repository (mode 600). Nothing secret is committed. Remove everything with
# ./openproject-down.sh.
set -euo pipefail

OLD_TAG="${1:-13.4.0-slim}"
NEW_TAG="${2:-14.0.0-slim}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STATE_DIR="${GAMMATRON_QUAL_STATE:-$HOME/.local/state/gammatron-qual}"
STATE_FILE="$STATE_DIR/openproject.json"
NET=gammatron-op-qual-net
PG=gammatron-op-pg15
PG_PORT=28432
OLD_NAME=gammatron-op-old
NEW_NAME=gammatron-op-new
OLD_PORT=28413
NEW_PORT=28414
READY_TIMEOUT_S="${READY_TIMEOUT_S:-600}"

command -v docker >/dev/null || { echo "docker not found" >&2; exit 1; }
docker info >/dev/null 2>&1 || { echo "docker daemon not reachable" >&2; exit 1; }
if docker ps -a --format '{{.Names}}' | grep -Eq "^($PG|$OLD_NAME|$NEW_NAME)$"; then
  echo "Containers from an earlier bring-up exist. Run ./openproject-down.sh first." >&2
  exit 1
fi

rand() { openssl rand -hex "$1"; }
PG_PASSWORD="$(rand 16)"
USER_PASSWORD="Aa1!$(rand 12)"
KEY_OLD="$(rand 48)"
KEY_NEW="$(rand 48)"

umask 077
mkdir -p "$STATE_DIR"

docker network inspect "$NET" >/dev/null 2>&1 || docker network create "$NET" >/dev/null
docker run -d --name "$PG" --network "$NET" -p "127.0.0.1:$PG_PORT:5432" \
  -e POSTGRES_USER=opqual -e POSTGRES_PASSWORD="$PG_PASSWORD" -e POSTGRES_DB=postgres \
  postgres:15 >/dev/null
for _ in $(seq 1 60); do
  docker exec "$PG" pg_isready -U opqual >/dev/null 2>&1 && break
  sleep 0.5
done
docker exec "$PG" psql -q -U opqual -d postgres -c "CREATE DATABASE op_old_qual;" -c "CREATE DATABASE op_new_qual;"

app_env() { # <db> <secret> <host port>
  printf '%s\n' -e RAILS_ENV=production \
    -e "DATABASE_URL=postgres://opqual:$PG_PASSWORD@$PG:5432/$1" \
    -e "SECRET_KEY_BASE=$2" -e OPENPROJECT_HTTPS=false \
    -e "OPENPROJECT_HOST__NAME=127.0.0.1:$3" \
    -e "STAGE2_USER_PASSWORD=$USER_PASSWORD"
}

start_release() { # <container> <tag> <db> <secret> <host port>
  local name="$1" tag="$2" db="$3" secret="$4" port="$5" env=()
  while IFS= read -r line; do env+=("$line"); done < <(app_env "$db" "$secret" "$port")
  echo "[$name] migrating $db on openproject/openproject:$tag"
  docker run --rm --network "$NET" "${env[@]}" "openproject/openproject:$tag" \
    bash -c 'bundle exec rake db:migrate' >"$STATE_DIR/$name-migrate.log" 2>&1
  docker run -d --name "$name" --network "$NET" -p "127.0.0.1:$port:8080" \
    -v "$HERE/seed_openproject_qual.rb:/tmp/seed_openproject_qual.rb:ro" \
    "${env[@]}" "openproject/openproject:$tag" >/dev/null
}

seed_release() { # <container> <host port> -> prints the seeder's JSON
  local name="$1" port="$2" waited=0
  until curl -sf -o /dev/null "http://127.0.0.1:$port/api/v3/configuration" \
     || [ "$(curl -s -o /dev/null -w '%{http_code}' "http://127.0.0.1:$port/api/v3/configuration")" = "401" ]; do
    waited=$((waited + 3))
    [ "$waited" -ge "$READY_TIMEOUT_S" ] && { echo "[$name] not ready after ${READY_TIMEOUT_S}s" >&2; return 1; }
    sleep 3
  done
  docker exec "$name" bundle exec rails runner /tmp/seed_openproject_qual.rb 2>"$STATE_DIR/$name-seed.log" \
    | sed -n 's/^STAGE2_SEED_JSON://p'
}

start_release "$OLD_NAME" "$OLD_TAG" op_old_qual "$KEY_OLD" "$OLD_PORT"
start_release "$NEW_NAME" "$NEW_TAG" op_new_qual "$KEY_NEW" "$NEW_PORT"
OLD_SEED="$(seed_release "$OLD_NAME" "$OLD_PORT")"
NEW_SEED="$(seed_release "$NEW_NAME" "$NEW_PORT")"
[ -n "$OLD_SEED" ] && [ -n "$NEW_SEED" ] || { echo "seeding printed no result; see $STATE_DIR/*-seed.log" >&2; exit 1; }

OLD_DIGEST="$(docker inspect --format '{{index .RepoDigests 0}}' "openproject/openproject:$OLD_TAG" 2>/dev/null || true)"
NEW_DIGEST="$(docker inspect --format '{{index .RepoDigests 0}}' "openproject/openproject:$NEW_TAG" 2>/dev/null || true)"

OLD_SEED="$OLD_SEED" NEW_SEED="$NEW_SEED" python3 - "$STATE_FILE" <<PY
import json, os, sys
state = {
    "schema": "gammatron-qual-openproject-state/v1",
    "username": "stage2_approver",
    "authorUsername": "stage2_author",
    "password": "$USER_PASSWORD",
    "old": {"tag": "$OLD_TAG", "image": "$OLD_DIGEST", "container": "$OLD_NAME",
            "url": "http://127.0.0.1:$OLD_PORT",
            "pgUrl": "postgres://opqual:$PG_PASSWORD@127.0.0.1:$PG_PORT/op_old_qual",
            "seed": json.loads(os.environ["OLD_SEED"])},
    "new": {"tag": "$NEW_TAG", "image": "$NEW_DIGEST", "container": "$NEW_NAME",
            "url": "http://127.0.0.1:$NEW_PORT",
            "pgUrl": "postgres://opqual:$PG_PASSWORD@127.0.0.1:$PG_PORT/op_new_qual",
            "seed": json.loads(os.environ["NEW_SEED"])},
}
with open(sys.argv[1], "w") as f:
    json.dump(state, f, indent=2)
PY
chmod 600 "$STATE_FILE"
echo "OpenProject $OLD_TAG on :$OLD_PORT and $NEW_TAG on :$NEW_PORT are seeded."
echo "State (tokens, passwords, status hrefs): $STATE_FILE"

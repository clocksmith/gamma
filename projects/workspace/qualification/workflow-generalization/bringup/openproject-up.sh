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
# Secrets reach the containers through env files, never as command-line arguments,
# which any process on the machine can list.
PG_ENV="$STATE_DIR/gammatron-op-pg.env"
printf 'POSTGRES_USER=opqual\nPOSTGRES_PASSWORD=%s\nPOSTGRES_DB=postgres\n' "$PG_PASSWORD" >"$PG_ENV"
docker run -d --name "$PG" --network "$NET" -p "127.0.0.1:$PG_PORT:5432" --env-file "$PG_ENV" postgres:15 >/dev/null
for _ in $(seq 1 60); do
  docker exec "$PG" pg_isready -U opqual >/dev/null 2>&1 && break
  sleep 0.5
done
# pg_isready also answers while PostgreSQL runs its own first initialisation, after which the
# server restarts; asking for the databases in that gap fails. Only the final server listens
# on TCP, so wait for two answers to SELECT 1 over TCP, a second apart.
pg_streak=0
for _ in $(seq 1 120); do
  if docker exec "$PG" sh -c 'PGPASSWORD="$POSTGRES_PASSWORD" psql -h 127.0.0.1 -U opqual -d postgres -Atc "SELECT 1"' >/dev/null 2>&1; then
    pg_streak=$((pg_streak + 1))
  else
    pg_streak=0
  fi
  [ "$pg_streak" -ge 2 ] && break
  sleep 1
done
[ "$pg_streak" -ge 2 ] || { echo "PostgreSQL did not become ready" >&2; exit 1; }
docker exec "$PG" psql -q -U opqual -d postgres -c "CREATE DATABASE op_old_qual;" -c "CREATE DATABASE op_new_qual;"

app_env_file() { # <container> <db> <secret> <host port> -> path of the env file
  local file="$STATE_DIR/$1.env"
  printf '%s\n' RAILS_ENV=production \
    "DATABASE_URL=postgres://opqual:$PG_PASSWORD@$PG:5432/$2" \
    "SECRET_KEY_BASE=$3" OPENPROJECT_HTTPS=false \
    "OPENPROJECT_HOST__NAME=127.0.0.1:$4" \
    "STAGE2_USER_PASSWORD=$USER_PASSWORD" >"$file"
  echo "$file"
}

start_release() { # <container> <tag> <db> <secret> <host port>
  local name="$1" tag="$2" db="$3" secret="$4" port="$5" env_file
  env_file="$(app_env_file "$name" "$db" "$secret" "$port")"
  echo "[$name] migrating $db on openproject/openproject:$tag"
  docker run --rm --network "$NET" --env-file "$env_file" "openproject/openproject:$tag" \
    bash -c 'bundle exec rake db:migrate' >"$STATE_DIR/$name-migrate.log" 2>&1
  docker run -d --name "$name" --network "$NET" -p "127.0.0.1:$port:8080" \
    -v "$HERE/seed_openproject_qual.rb:/tmp/seed_openproject_qual.rb:ro" \
    --env-file "$env_file" "openproject/openproject:$tag" >/dev/null
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
rm -f "$STATE_DIR"/gammatron-op-*.env

# Settle: a release that has only just answered can still reset a connection.
# Require five authenticated answers in a row from each release before handing over.
python3 - "$STATE_FILE" <<'PY'
import base64, json, sys, time, urllib.request
state = json.load(open(sys.argv[1]))
for side in ("old", "new"):
    release = state[side]
    token = base64.b64encode(("apikey:" + release["seed"]["approverToken"]).encode()).decode()
    streak, deadline = 0, time.time() + 120
    while streak < 5:
        if time.time() > deadline:
            sys.exit(f"{release['container']} did not settle: no five answers in a row within 120 s")
        try:
            request = urllib.request.Request(release["url"] + "/api/v3/users/me", headers={"Authorization": "Basic " + token})
            streak = streak + 1 if urllib.request.urlopen(request, timeout=20).status == 200 else 0
        except Exception:
            streak = 0
        time.sleep(1)
PY
echo "OpenProject $OLD_TAG on :$OLD_PORT and $NEW_TAG on :$NEW_PORT are seeded."
echo "State (tokens, passwords, status hrefs): $STATE_FILE"

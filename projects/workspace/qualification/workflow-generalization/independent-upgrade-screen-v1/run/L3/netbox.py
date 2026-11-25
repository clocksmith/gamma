"""NetBox bring-up and set-up shared by cases L2 and L3 (the two directories hold identical copies).

One stack is: PostgreSQL 16, one Redis (database 0 for queues, 1 for the cache) and one
NetBox container from the community image, all pulled by the digests in the sealed list,
on their own network, NetBox published on 127.0.0.1 only. Every password, the Django
secret key and the superuser API token are generated per stack.
"""
import time

import lib

PG_REF, REDIS_REF = "postgres:16-alpine", "redis:7-alpine"
PG_REPO, REDIS_REPO, NB_REPO = "postgres", "redis", "netboxcommunity/netbox"


class Stack:
    def __init__(self, scope, port, pins, netbox_ref):
        self.scope, self.port, self.pins, self.ref = scope, port, pins, netbox_ref
        self.base = "http://127.0.0.1:%d" % port
        low = scope.lower()
        self.net, self.pg, self.redis, self.app = ("iu1b-%s-net" % low, "iu1b-%s-pg" % low,
                                                   "iu1b-%s-redis" % low, "iu1b-%s-app" % low)
        self.secrets = {"pg": lib.new_secret(), "redis": lib.new_secret(), "django": lib.new_secret(32),
                        "admin_pass": lib.new_secret(12), "admin_token": lib.new_secret(20),
                        "engineer_pass": "Pw-" + lib.new_secret(12)}
        lib.add_secret(self.secrets["engineer_pass"])
        self.admin = {"Authorization": "Token " + self.secrets["admin_token"], "Accept": "application/json"}

    def bring_up(self):
        sec = self.secrets
        self.started_utc = lib.utc_now()
        lib.network_create(self.scope, self.net)
        lib.run_container(self.scope, self.pg, self.pins[PG_REF]["pulled_ref"], network=self.net,
                          alias="postgres", env={"POSTGRES_DB": "netbox", "POSTGRES_USER": "netbox",
                                                 "POSTGRES_PASSWORD": sec["pg"]})
        lib.run_container(self.scope, self.redis, self.pins[REDIS_REF]["pulled_ref"], network=self.net,
                          alias="redis", cmd=["redis-server", "--requirepass", sec["redis"]])
        deadline = time.time() + 600
        while lib.docker("exec", self.pg, "pg_isready", "-U", "netbox", "-d", "netbox",
                         check=False).returncode != 0:
            deadline += lib.wait_hold()
            if time.time() > deadline:
                raise RuntimeError("PostgreSQL not ready")
            time.sleep(2)
        lib.run_container(self.scope, self.app, self.pins[self.ref]["pulled_ref"], network=self.net,
                          publish=[(self.port, 8080)], env={
            "DB_HOST": "postgres", "DB_NAME": "netbox", "DB_USER": "netbox", "DB_PASSWORD": sec["pg"],
            "REDIS_HOST": "redis", "REDIS_PASSWORD": sec["redis"], "REDIS_DATABASE": "0",
            "REDIS_CACHE_HOST": "redis", "REDIS_CACHE_PASSWORD": sec["redis"], "REDIS_CACHE_DATABASE": "1",
            "SECRET_KEY": sec["django"], "ALLOWED_HOSTS": "*", "MAX_DB_WAIT_TIME": "600",
            "SKIP_SUPERUSER": "false", "SUPERUSER_NAME": "admin", "SUPERUSER_EMAIL": "admin@example.test",
            "SUPERUSER_PASSWORD": sec["admin_pass"], "SUPERUSER_API_TOKEN": sec["admin_token"]})
        # First start applies every migration; the API answers only after that.
        lib.wait_http(self.base + "/api/status/", headers=self.admin, timeout=3600, interval=5)
        self.ready_utc = lib.utc_now()
        _, text, _ = lib.http("GET", self.base + "/api/status/", headers=self.admin)
        status = lib.json.loads(text)
        self.reported = {k: status.get(k) for k in ("netbox-version", "django-version", "python-version")}
        return self

    def sql(self, query):
        """Read straight from PostgreSQL in the database container. Raw lines, header first."""
        out = lib.docker("exec", "-e", "PGPASSWORD=" + self.secrets["pg"], self.pg, "psql", "-U", "netbox",
                         "-d", "netbox", "-A", "-F", "|", "-P", "footer=off", "-P", "null=NULL",
                         "-c", query).stdout
        return out.rstrip("\n").split("\n") if out.strip() else []

    def conditions(self):
        return {
            "install": "fresh install: the image applies all migrations to an empty PostgreSQL database on first start; no in-place upgrade",
            "reported_versions": self.reported,
            "postgres": self.sql("SELECT version(), current_setting('TimeZone') AS time_zone, now()"),
            "container_memory": [m for m in lib.memory_snapshot() if m.startswith("iu1b-")],
            "configuration": "image defaults; no plugins; no worker container (not needed for REST writes)",
        }

    def create_engineer(self, rec, permissions):
        """A non-superuser with object permissions and an API token, created by the superuser through the API.

        permissions: list of (name, [object types], [actions]).
        """
        status, user, text = rec.call("superuser creates the engineer account", "POST", "/api/users/users/",
                                      body={"username": "neteng", "password": self.secrets["engineer_pass"]},
                                      headers=self.admin)
        if status != 201:
            raise RuntimeError("user: %s %s" % (status, text[:300]))
        for name, types, actions in permissions:
            status, _, text = rec.call("superuser grants permission '%s'" % name, "POST",
                                       "/api/users/permissions/",
                                       body={"name": name, "object_types": types, "actions": actions,
                                             "users": [user["id"]]}, headers=self.admin)
            if status != 201:
                raise RuntimeError("permission: %s %s" % (status, text[:300]))
        status, token, text = rec.call("superuser issues the engineer's API token", "POST", "/api/users/tokens/",
                                       body={"user": user["id"]}, headers=self.admin, excerpt=200)
        if status != 201:
            raise RuntimeError("token: %s %s" % (status, text[:300]))
        key = lib.add_secret(token["key"])
        rec.calls[-1]["response_body_excerpt"] = lib.redact_text(rec.calls[-1]["response_body_excerpt"])
        self.engineer = {"Authorization": "Token " + key, "Accept": "application/json"}
        self.engineer_user_id = user["id"]
        return user["id"]


def classify(a, b, c):
    """Mechanical disposition by the table in the protocol README."""
    a_ok = sum(1 for o in a if o["reported_success"] and o["stored_equals_right"])
    c_ok = sum(1 for o in c if o["stored_equals_right"])
    kinds = []
    for o in b:
        if not o["reported_success"]:
            kinds.append("loud-failure")
        elif o["stored_equals_right"]:
            kinds.append("self-healing")
        else:
            kinds.append("silent-wrong-write")
    summary = {"gate_A_pass": "%d of %d" % (a_ok, len(a)), "gate_B_per_repeat": kinds,
               "gate_C_pass": "%d of %d" % (c_ok, len(c))}
    if not a or a_ok != len(a):
        return "setup-block", summary
    if len(set(kinds)) != 1:
        return "mixed", summary
    if kinds[0] == "silent-wrong-write" and c_ok != len(c):
        return "mixed", summary
    return kinds[0], summary

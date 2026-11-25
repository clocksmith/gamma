#!/usr/bin/env python3
"""N7: NocoDB 0.107.5 -> 0.108.0, recording a site visit at 10:00 New York time through the REST API.

One command runs gates A, B and C, three repeats each, every repeat on an instance
started from nothing, and writes ../../results/N7.json:

    SCREEN_SCRATCH=/some/dir [SCREEN_HOLD_FILE=/path/HOLD] \
    [PLAYWRIGHT_MODULE=/path/to/node_modules/playwright] python3 run.py

The sealed list asks for three reads of the stored value: the SQLite file, an API read,
and what the page shows in a browser set to America/New_York. The page read needs
Playwright with a Chromium build; without PLAYWRIGHT_MODULE it is recorded as not done.

The old workflow's request, the correct path and the right value come from the sealed
list (screen-list.json, case N7).
"""
import argparse
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib  # noqa: E402

CASE = "N7"
PORT = 28650
BASE = "http://127.0.0.1:%d" % PORT
REPO = "nocodb/nocodb"
FROM_REF, TO_REF = "nocodb/nocodb:0.107.5", "nocodb/nocodb:0.108.0"
VOLUME, APP = "iu1b-n7-data", "iu1b-n7-app"
HERE = os.path.dirname(os.path.abspath(__file__))
VIEWER_TZ = "America/New_York"

OLD_WORKFLOW_BODY = {"Title": "visit", "When": "2023-06-01 10:00:00"}          # sealed
CORRECT_PATH_BODY = {"Title": "visit", "When": "2023-06-01 14:00:00+00:00"}    # sealed
RIGHT_TEXT_FROM = "2023-06-01 10:00:00"          # sealed, from-version
RIGHT_INSTANT_TO = "2023-06-01T14:00:00Z"        # sealed, to-version
RIGHT_SHOWN = "2023-06-01 10:00"                 # 10:00 on 1 June 2023 for the New York office

SENSITIVE = re.compile(r'"(password|salt|refresh_token|invite_token|token_version|email_verification_token|'
                       r'reset_password_token|token)":\s*"[^"]*"')


def scrub(rec):
    for call in rec.calls:
        call["response_body_excerpt"] = SENSITIVE.sub(r'"\1":"<redacted>"', call["response_body_excerpt"])
    return rec.calls


def start(pins, ref, jwt):
    lib.volume_create(CASE, VOLUME)
    lib.run_container(CASE, APP, pins[ref]["pulled_ref"], publish=[(PORT, 8080)],
                      mounts=[VOLUME + ":/usr/app/data"],
                      env={"NC_AUTH_JWT_SECRET": jwt, "NC_DISABLE_TELE": "true", "NC_PUBLIC_URL": BASE})
    lib.wait_http(BASE + "/api/v1/health", timeout=900, interval=2)
    _, text, _ = lib.http("GET", BASE + "/api/v1/db/meta/nocodb/info")
    clock = lib.docker("exec", APP, "sh", "-c", "echo TZ=[$TZ] $(date +%Z) $(date -u +%Y-%m-%dT%H:%M:%SZ)",
                       check=False).stdout.strip()
    return {"image": ref, "ready_utc": lib.utc_now(), "reported_version": lib.json.loads(text).get("version"),
            "container_clock": clock}


def read_db(tag, table):
    """Copy the SQLite file out of the data volume and query the copy read-only."""
    dest = os.path.join(lib.scratch_dir(CASE), "dbcopy-" + tag)
    shutil.rmtree(dest, ignore_errors=True)
    os.makedirs(dest)
    lib.docker("cp", APP + ":/usr/app/data/.", dest)
    con = sqlite3.connect("file:%s?mode=ro" % os.path.join(dest, "noco.db"), uri=True)
    query = 'SELECT id, title, "when", typeof("when") AS when_type FROM "%s" ORDER BY id' % table
    rows = [dict(zip(("id", "title", "when", "when_type"), r)) for r in con.execute(query)]
    ddl = con.execute("SELECT sql FROM sqlite_master WHERE name = ?", (table,)).fetchone()[0]
    con.close()
    shutil.rmtree(dest, ignore_errors=True)
    return {"query": query, "rows": rows, "table_ddl": ddl}


def sign(rec, step, path, email, password):
    status, body, text = rec.call(step, "POST", path, body={"email": email, "password": password}, excerpt=200)
    if status != 200:
        raise RuntimeError("%s: %s %s" % (step, status, text[:200]))
    return {"xc-auth": lib.add_secret(body["token"])}


def set_up(secrets):
    rec = lib.Recorder(BASE)
    owner = sign(rec, "first user (owner) signs up", "/api/v1/auth/user/signup", "owner@example.test", secrets["owner"])
    sign(rec, "second user signs up", "/api/v1/auth/user/signup", "editor@example.test", secrets["editor"])
    status, project, text = rec.call("owner creates the base", "POST", "/api/v1/db/meta/projects/",
                                     body={"title": "Field office"}, headers=owner, excerpt=200)
    if status != 200:
        raise RuntimeError("project: %s %s" % (status, text[:300]))
    pid = project["id"]
    status, table, text = rec.call("owner creates table visits with a DateTime column", "POST",
                                   "/api/v1/db/meta/projects/%s/tables" % pid, headers=owner, excerpt=200, body={
        "table_name": "visits", "title": "visits", "columns": [
            {"column_name": "id", "title": "Id", "uidt": "ID", "dt": "integer", "pk": True, "ai": True, "rqd": True},
            {"column_name": "title", "title": "Title", "uidt": "SingleLineText", "pv": True},
            {"column_name": "when", "title": "When", "uidt": "DateTime"}]})
    if status != 200:
        raise RuntimeError("table: %s %s" % (status, text[:300]))
    status, _, text = rec.call("owner adds the second user to the base as editor", "POST",
                               "/api/v1/db/meta/projects/%s/users" % pid,
                               body={"email": "editor@example.test", "roles": "editor"}, headers=owner)
    if status != 200:
        raise RuntimeError("invite: %s %s" % (status, text[:300]))
    editor = sign(rec, "editor signs in (xc-auth token)", "/api/v1/auth/user/signin",
                  "editor@example.test", secrets["editor"])
    _, me, _ = rec.call("editor's role in the base", "GET", "/api/v1/auth/user/me?project_id=%s" % pid,
                        headers=editor, excerpt=0)
    _, users, _ = rec.call("owner lists the base's users", "GET", "/api/v1/db/meta/projects/%s/users" % pid,
                           headers=owner, excerpt=0)
    members = [{k: u.get(k) for k in ("email", "roles", "main_roles")}
               for u in (users or {}).get("users", {}).get("list", [])]
    return {"calls": scrub(rec), "project": pid, "table_title": "visits", "table_name": table["table_name"],
            "columns": [{k: c.get(k) for k in ("title", "column_name", "uidt", "dt")} for c in table["columns"]],
            "editor_roles_in_base": (me or {}).get("roles"), "base_users": members,
            "owner": owner, "editor": editor}


def page_read(setup, secrets):
    """What the grid shows to the editor in a browser set to America/New_York."""
    module = os.environ.get("PLAYWRIGHT_MODULE")
    if not module:
        return {"done": False, "reason": "PLAYWRIGHT_MODULE not set"}
    env = dict(os.environ, NC_PASSWORD=secrets["editor"])
    proc = subprocess.run(["node", os.path.join(HERE, "page_read.cjs"), BASE, "editor@example.test",
                           setup["project"], setup["table_title"], VIEWER_TZ],
                          capture_output=True, text=True, env=env, timeout=600)
    try:
        out = lib.json.loads(proc.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        return {"done": False, "reason": "page reader gave no result",
                "stderr": lib.redact_text(proc.stderr)[-300:]}
    out["done"] = bool(out.get("ok"))
    return out


OFFSET = re.compile(r"^(\d{4}-\d{2}-\d{2})[ T](\d{2}:\d{2}:\d{2})(?:\.\d+)?\s*(Z|[+-]\d{2}:?\d{2})$")


def instant_of(text):
    """UTC instant of a stored or returned text, only when the text itself carries a zone."""
    match = OFFSET.match(text or "")
    if not match:
        return None
    date, clock, zone = match.groups()
    if zone == "Z":
        minutes = 0
    else:
        sign_ = -1 if zone[0] == "-" else 1
        digits = zone[1:].replace(":", "")
        minutes = sign_ * (int(digits[:2]) * 60 + int(digits[2:]))
    stamp = time.strptime(date + " " + clock, "%Y-%m-%d %H:%M:%S")
    import calendar
    epoch = calendar.timegm(stamp) - minutes * 60
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(epoch))


def observe(gate, secrets, setup, body, description, to_version, tag):
    watch = lib.HoldWatch()
    rec = lib.Recorder(BASE)
    data_path = "/api/v1/db/data/noco/%s/%s" % (setup["project"], setup["table_title"])
    db_before = read_db(tag + "-before", setup["table_name"])
    status, parsed, text = rec.call(description, "POST", data_path, body=body, headers=setup["editor"])
    new_id = parsed.get("Id") if status == 200 and isinstance(parsed, dict) else None
    time.sleep(2)
    db_after = read_db(tag + "-after", setup["table_name"])
    row = next((r for r in db_after["rows"] if r["id"] == new_id), None)
    stored_text = row["when"] if row else None
    # Independent read with a different credential: the owner lists the rows.
    _, listed, _ = rec.call("API read by the owner", "GET", data_path, headers=setup["owner"], excerpt=400)
    api_value = next((r.get("When") for r in (listed or {}).get("list", []) if r.get("Id") == new_id), None)
    page = page_read(setup, secrets)
    index = next((i for i, r in enumerate(db_after["rows"]) if r["id"] == new_id), None)
    shown = None
    if page.get("done") and index is not None:
        shown = next((c["shown"] for c in page.get("when_cells", [])
                      if c["testid"] == "cell-When-%d" % index), None)
    if to_version:
        from_db, from_api = instant_of(stored_text), instant_of(api_value)
        stored = {"sqlite_text": stored_text, "instant_from_sqlite_text": from_db,
                  "api_read_by_owner": api_value, "instant_from_api_read": from_api,
                  "page_shows_in_new_york": shown}
        instant = from_db or from_api
        stored["instant_used"] = instant
        stored["instant_source"] = ("the SQLite text carries a zone" if from_db else
                                    "the SQLite text carries no zone; the application's own read is used"
                                    if from_api else "no zone in either read")
        right = {"instant": RIGHT_INSTANT_TO, "page_shows_in_new_york": RIGHT_SHOWN}
        # None when no read carries a zone: the instant cannot be told, so it is not called wrong.
        equal = (instant == RIGHT_INSTANT_TO) if instant else None
    else:
        stored = {"sqlite_text": stored_text, "api_read_by_owner": api_value, "page_shows_in_new_york": shown}
        right = {"sqlite_text": RIGHT_TEXT_FROM, "page_shows_in_new_york": RIGHT_SHOWN}
        equal = stored_text == RIGHT_TEXT_FROM
    return {
        "gate": gate, "acting_user": "editor@example.test (role editor in the base; org-level viewer)",
        "calls": scrub(rec),
        "application_answer": {"status": status, "body_excerpt": text[:500]},
        "reported_success": status == 200, "success_criterion": "HTTP 200",
        "returned_id": new_id,
        "db_before": db_before, "db_after": db_after,
        "page_read": page,
        "stored_value": stored, "right_value": right,
        "stored_equals_right": equal,
        "page_agrees_with_right": (shown == RIGHT_SHOWN) if shown is not None else None,
        "hold": watch.record(),
    }


def make_repeat(kind, pins):
    def run(repeat):
        secrets = {"jwt": lib.new_secret(24), "owner": "Aa1!" + lib.new_secret(10), "editor": "Aa1!" + lib.new_secret(10)}
        lib.add_secret(secrets["owner"])
        lib.add_secret(secrets["editor"])
        lib.log("N7 %s repeat %d" % (kind, repeat))
        ref = FROM_REF if kind == "from" else TO_REF
        evidence = {"repeat": repeat, "kind": kind, "started_utc": lib.utc_now(), "observations": []}
        evidence["instance"] = start(pins, ref, secrets["jwt"])
        setup = set_up(secrets)
        evidence["setup"] = {k: v for k, v in setup.items() if k not in ("owner", "editor")}
        if kind == "from":
            evidence["observations"].append(observe(
                "A", secrets, setup, OLD_WORKFLOW_BODY, "old workflow exactly as sealed, from-version",
                False, "from-%d" % repeat))
        else:
            evidence["observations"].append(observe(
                "B", secrets, setup, OLD_WORKFLOW_BODY, "old workflow exactly as sealed, to-version",
                True, "to-b-%d" % repeat))
            evidence["observations"].append(observe(
                "C", secrets, setup, CORRECT_PATH_BODY, "correct path as sealed, to-version, second row",
                True, "to-c-%d" % repeat))
        evidence["container_memory"] = [m for m in lib.memory_snapshot() if m.startswith("iu1b-")]
        return evidence
    return run


def classify(a, b, c):
    """Mechanical disposition by the table in the protocol README."""
    a_ok = sum(1 for o in a if o["reported_success"] and o["stored_equals_right"])
    c_ok = sum(1 for o in c if o["stored_equals_right"])
    kinds = []
    for o in b:
        if not o["reported_success"]:
            kinds.append("loud-failure")
        elif o["stored_equals_right"] is None:
            kinds.append("not-distinguishable")
        elif o["stored_equals_right"]:
            kinds.append("self-healing")
        else:
            kinds.append("silent-wrong-write")
    summary = {"gate_A_pass": "%d of %d" % (a_ok, len(a)), "gate_B_per_repeat": kinds,
               "gate_C_pass": "%d of %d" % (c_ok, len(c))}
    if not a or a_ok != len(a):
        return "setup-block", summary
    if len(set(kinds)) != 1 or kinds[0] == "not-distinguishable":
        return "mixed", summary
    if kinds[0] == "silent-wrong-write" and c_ok != len(c):
        return "mixed", summary
    return kinds[0], summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--reuse", action="store_true",
                        help="keep repeats already recorded in the scratch directory and run only the missing ones")
    parser.add_argument("--out", default=os.path.join(HERE, "..", "..", "results", "N7.json"))
    args = parser.parse_args()
    sealed = lib.sealed_case(CASE)
    scratch = lib.scratch_dir(CASE)
    started = lib.utc_now()
    lib.wait_hold()
    lib.teardown(CASE)
    pins, images = lib.pin_images(sealed, ((FROM_REF, REPO), (TO_REF, REPO)))

    runs, reused = {}, []
    for kind in ("from", "to"):
        runs[kind] = []
        for i in range(1, args.repeats + 1):
            path = os.path.join(scratch, "%s-%d.json" % (kind, i))
            if args.reuse and os.path.exists(path):
                with open(path) as handle:
                    runs[kind].append(lib.json.load(handle))
                reused.append("%s repeat %d" % (kind, i))
                continue
            runs[kind].append(lib.run_repeat(CASE, make_repeat(kind, pins), i))
            lib.write_json(path, runs[kind][-1])

    def pick(repeats, gate):
        return [o for r in repeats for o in r["observations"] if o["gate"] == gate]

    a, b, c = pick(runs["from"], "A"), pick(runs["to"], "B"), pick(runs["to"], "C")
    disposition, summary = classify(a, b, c)
    predicted = sealed["predicted_disposition"]

    def short(obs):
        return [{"repeat": i + 1, "status": o["application_answer"]["status"],
                 "body": o["application_answer"]["body_excerpt"][:160],
                 "stored_value": o["stored_value"], "right_value": o["right_value"],
                 "stored_equals_right": o["stored_equals_right"],
                 "page_agrees_with_right": o["page_agrees_with_right"]} for i, o in enumerate(obs)]

    result = {
        "schema": "gammatron-real-upgrade-screen-result/v1",
        "case_id": CASE, "screen_lane": "iu1-b",
        "app": sealed["app"], "from_version": sealed["from_version"], "to_version": sealed["to_version"],
        "images": images,
        "conditions": {
            "host": "macOS on Apple Silicon, Docker Desktop, linux/arm64 containers, port bound to 127.0.0.1",
            "install": "every repeat is a fresh install with a new SQLite file; no in-place upgrade was run",
            "database": "SQLite file in a labelled Docker volume; read from a copy taken with docker cp",
            "time_zone": "container time zone UTC (image default, no TZ set); the viewer's browser is set to "
                         "America/New_York (UTC-4 on 1 June 2023)",
            "acting_role": "editor@example.test, added to the base by its owner with role editor; "
                           "the request carries the editor's xc-auth token",
            "settings_that_matter": "defaults; telemetry off",
            "page_read": "headless Chromium through Playwright, signed in as the editor, time zone America/New_York",
            "gate_B_and_C": "the same to-version instance serves B (first row) and C (second row)",
        },
        "sealed": {
            "old_workflow_steps": sealed["old_workflow_steps"],
            "correct_path_on_to_version": sealed["correct_path_on_to_version"],
            "database_outcome": sealed["database_outcome"],
            "prediction_condition": sealed["prediction_condition"],
            "predicted_disposition": predicted, "prediction_detail": sealed["prediction_detail"],
        },
        "right_value_as_applied": {
            "from_version": "SQLite text of When equals '2023-06-01 10:00:00' (sealed); the page is expected to show 10:00",
            "to_version": "the stored instant equals 2023-06-01T14:00:00Z (sealed). The instant is taken from the "
                          "SQLite text when that text carries a zone, otherwise from the owner's API read; "
                          "the page read in a New York browser is recorded beside it",
        },
        "gates": {
            "A": {"what": "old workflow on the from-version", "pass": summary["gate_A_pass"],
                  "observations_in_short": short(a)},
            "B": {"what": "identical steps on the to-version", "per_repeat": summary["gate_B_per_repeat"],
                  "observations_in_short": short(b)},
            "C": {"what": "correct path on the to-version, second row", "pass": summary["gate_C_pass"],
                  "observations_in_short": short(c)},
        },
        "disposition": disposition,
        "disposition_rule": "protocol README table, applied mechanically to the stored values below",
        "prediction": {"sealed": predicted, "observed": disposition, "right": predicted == disposition},
        "deviations": [],
        "flags": [],
        "repeats_taken_from_an_earlier_execution_of_this_script": reused,
        "repeats": runs,
        "times_utc": {"started": started, "finished": lib.utc_now(), "clock": "date -u on the host"},
        "free_disk_gib_at_end": lib.free_disk_gib(),
    }
    lib.write_json(args.out, result)
    lib.teardown(CASE)
    print(disposition, summary)


if __name__ == "__main__":
    main()

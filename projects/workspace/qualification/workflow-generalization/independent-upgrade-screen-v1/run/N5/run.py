#!/usr/bin/env python3
"""N5: Vikunja 0.23.0 -> 0.24.0, moving a task to the Done column through the REST API.

One command runs gates A, B and C, three repeats each, and writes ../../results/N5.json:

    SCREEN_SCRATCH=/some/dir [SCREEN_HOLD_FILE=/path/HOLD] python3 run.py

Every repeat starts from an empty data volume. As the sealed list prescribes for this
case, the to-version is reached by an in-place upgrade: 0.23.0 is started on the empty
volume, the case is set up, the container is stopped and 0.24.0 is started on the same
volume, so the column numbers the workflow learned carry over.

A supplementary block repeats gate B on a fresh install of 0.24.0 (set up through
0.24.0's own API); it does not decide the disposition.
"""
import argparse
import os
import shutil
import sqlite3
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib  # noqa: E402

CASE = "N5"
PORT = 28620
BASE = "http://127.0.0.1:%d" % PORT
REPO = "vikunja/vikunja"
FROM_REF, TO_REF = "vikunja/vikunja:0.23.0", "vikunja/vikunja:0.24.0"
VOLUME, APP = "iu1b-n5-data", "iu1b-n5-app"
TASK_TITLE, TASK2_TITLE = "Ship order 1042", "Ship order 1043"


def old_workflow_body(project, done_bucket):
    """The task's fields as set up, plus the Done column the workflow learned."""
    return {"title": TASK_TITLE, "description": "", "done": False,
            "project_id": project, "bucket_id": done_bucket}


def start(pins, ref, jwt, first):
    if first:
        lib.volume_create(CASE, VOLUME)
        # The application runs as uid 1000; a new volume belongs to root.
        lib.docker("run", "--rm", "--label", lib.LABEL, "--label", lib.case_label(CASE),
                   "-v", VOLUME + ":/db", "--entrypoint", "chown", pins[FROM_REF]["pulled_ref"],
                   "-R", "1000:1000", "/db")
    lib.run_container(CASE, APP, pins[ref]["pulled_ref"], publish=[(PORT, 3456)],
                      mounts=[VOLUME + ":/db"], env={
        "VIKUNJA_DATABASE_TYPE": "sqlite", "VIKUNJA_DATABASE_PATH": "/db/vikunja.db",
        "VIKUNJA_SERVICE_JWTSECRET": jwt, "VIKUNJA_SERVICE_TIMEZONE": "UTC",
        "VIKUNJA_SERVICE_FRONTENDURL": BASE + "/", "VIKUNJA_SERVICE_PUBLICURL": BASE + "/",
        "VIKUNJA_MAILER_ENABLED": "false"})
    lib.wait_http(BASE + "/api/v1/info", timeout=600, interval=2)
    _, text, _ = lib.http("GET", BASE + "/api/v1/info")
    return {"image": ref, "ready_utc": lib.utc_now(), "reported_version": lib.json.loads(text).get("version")}


def stop_app():
    lib.docker("stop", "-t", "30", APP)
    lib.docker("rm", "-v", APP)


def read_db(tag, queries, settle=0):
    """Copy the SQLite file out of the data volume and query the copy read-only."""
    time.sleep(settle)  # lets the application finish any work it does after answering
    dest = os.path.join(lib.scratch_dir(CASE), "dbcopy-" + tag)
    shutil.rmtree(dest, ignore_errors=True)
    os.makedirs(dest)
    lib.docker("cp", APP + ":/db/.", dest)
    con = sqlite3.connect("file:%s?mode=ro" % os.path.join(dest, "vikunja.db"), uri=True)
    con.row_factory = sqlite3.Row
    out = {}
    for name, query in queries.items():
        out[name] = {"query": query, "rows": [dict(r) for r in con.execute(query)]}
    con.close()
    shutil.rmtree(dest, ignore_errors=True)
    return out


def login(rec, step, user, password):
    status, body, text = rec.call(step, "POST", "/api/v1/login", body={"username": user, "password": password})
    if status != 200:
        raise RuntimeError("login failed for %s: %s %s" % (user, status, text[:200]))
    return {"Authorization": "Bearer " + lib.add_secret(body["token"])}


def register_users(rec, secrets):
    for user in ("owner1", "member1"):
        status, _, text = rec.call("register %s" % user, "POST", "/api/v1/register", body={
            "username": user, "email": user + "@example.test", "password": secrets[user]})
        if status != 200:
            raise RuntimeError("register failed: %s %s" % (status, text[:200]))


def set_up_023(secrets):
    """Set-up on 0.23.0: board with To-Do and Done, Done as the done column, two tasks, one member."""
    rec = lib.Recorder(BASE)
    register_users(rec, secrets)
    owner = login(rec, "owner logs in", "owner1", secrets["owner1"])
    status, project, text = rec.call("owner creates the project", "PUT", "/api/v1/projects",
                                     body={"title": "Order desk"}, headers=owner)
    if status != 201:
        raise RuntimeError("project: %s %s" % (status, text[:200]))
    pid = project["id"]
    _, buckets, _ = rec.call("owner lists the board columns", "GET", "/api/v1/projects/%d/buckets" % pid,
                             headers=owner)
    first = buckets[0]
    rec.call("owner renames the default column to To-Do", "POST",
             "/api/v1/projects/%d/buckets/%d" % (pid, first["id"]),
             body={"title": "To-Do", "position": first["position"]}, headers=owner)
    status, done, text = rec.call("owner adds the Done column", "PUT", "/api/v1/projects/%d/buckets" % pid,
                                  body={"title": "Done"}, headers=owner)
    if status != 201:
        raise RuntimeError("done bucket: %s %s" % (status, text[:200]))
    status, _, text = rec.call("owner sets To-Do as default and Done as the done column", "POST",
                               "/api/v1/projects/%d" % pid,
                               body={"title": "Order desk", "default_bucket_id": first["id"],
                                     "done_bucket_id": done["id"]}, headers=owner)
    if status != 200:
        raise RuntimeError("project update: %s %s" % (status, text[:200]))
    tasks = []
    for title in (TASK_TITLE, TASK2_TITLE):
        status, task, text = rec.call("owner creates task '%s'" % title, "PUT",
                                      "/api/v1/projects/%d/tasks" % pid, body={"title": title}, headers=owner)
        if status != 201:
            raise RuntimeError("task: %s %s" % (status, text[:200]))
        tasks.append(task["id"])
    status, _, text = rec.call("owner gives member1 write access", "PUT", "/api/v1/projects/%d/users" % pid,
                               body={"user_id": "member1", "right": 1}, headers=owner)
    if status != 201:
        raise RuntimeError("share: %s %s" % (status, text[:200]))
    return {"calls": rec.calls, "project": pid, "todo_bucket": first["id"], "done_bucket": done["id"],
            "task": tasks[0], "task2": tasks[1]}


def set_up_024_fresh(secrets):
    """Set-up on a fresh 0.24.0: the default board already has To-Do, Doing and Done."""
    rec = lib.Recorder(BASE)
    register_users(rec, secrets)
    owner = login(rec, "owner logs in", "owner1", secrets["owner1"])
    status, project, text = rec.call("owner creates the project", "PUT", "/api/v1/projects",
                                     body={"title": "Order desk"}, headers=owner)
    if status != 201:
        raise RuntimeError("project: %s %s" % (status, text[:200]))
    pid = project["id"]
    _, views, _ = rec.call("owner lists the project views", "GET", "/api/v1/projects/%d/views" % pid,
                           headers=owner)
    board = [v for v in views if v["view_kind"] == "kanban"][0]
    _, buckets, _ = rec.call("owner lists the board columns", "GET",
                             "/api/v1/projects/%d/views/%d/buckets" % (pid, board["id"]), headers=owner)
    first = buckets[0]
    bucket_path = "/api/v1/projects/%d/views/%d/buckets" % (pid, board["id"])
    status, _, text = rec.call("owner renames the default column to To-Do", "POST",
                               "%s/%d" % (bucket_path, first["id"]),
                               body={"title": "To-Do", "position": first["position"]}, headers=owner)
    if status != 200:
        raise RuntimeError("rename: %s %s" % (status, text[:200]))
    status, done, text = rec.call("owner adds the Done column", "PUT", bucket_path,
                                  body={"title": "Done"}, headers=owner)
    if status != 201:
        raise RuntimeError("done bucket: %s %s" % (status, text[:200]))
    view_body = dict(board, default_bucket_id=first["id"], done_bucket_id=done["id"])
    status, board, text = rec.call("owner sets To-Do as default and Done as the done column of the board view",
                                   "POST", "/api/v1/projects/%d/views/%d" % (pid, board["id"]),
                                   body=view_body, headers=owner)
    if status != 200 or board["done_bucket_id"] != done["id"] or board["default_bucket_id"] != first["id"]:
        raise RuntimeError("view update: %s %s" % (status, text[:300]))
    buckets = [{"id": first["id"], "title": "To-Do"}, {"id": done["id"], "title": "Done"}]
    tasks = []
    for title in (TASK_TITLE, TASK2_TITLE):
        status, task, text = rec.call("owner creates task '%s'" % title, "PUT",
                                      "/api/v1/projects/%d/tasks" % pid, body={"title": title}, headers=owner)
        if status != 201:
            raise RuntimeError("task: %s %s" % (status, text[:200]))
        tasks.append(task["id"])
    status, _, text = rec.call("owner gives member1 write access", "PUT", "/api/v1/projects/%d/users" % pid,
                               body={"user_id": "member1", "right": 1}, headers=owner)
    if status != 201:
        raise RuntimeError("share: %s %s" % (status, text[:200]))
    return {"calls": rec.calls, "project": pid, "board_view": board["id"],
            "todo_bucket": board["default_bucket_id"], "done_bucket": board["done_bucket_id"],
            "board_columns": [{"id": b["id"], "title": b["title"]} for b in buckets],
            "task": tasks[0], "task2": tasks[1]}


Q_023 = {
    "tasks": "SELECT id, title, done, project_id, bucket_id FROM tasks ORDER BY id",
    "buckets": "SELECT id, title, project_id FROM buckets ORDER BY id",
    "projects": "SELECT id, title, default_bucket_id, done_bucket_id FROM projects ORDER BY id",
}
Q_024 = {
    "tasks": "SELECT id, title, done, project_id FROM tasks ORDER BY id",
    "task_buckets": "SELECT task_id, bucket_id, project_view_id FROM task_buckets ORDER BY task_id, project_view_id",
    "buckets": "SELECT id, title, project_view_id FROM buckets ORDER BY id",
    "project_views": "SELECT id, title, project_id, view_kind, default_bucket_id, done_bucket_id "
                     "FROM project_views ORDER BY id",
}


def stored_023(db, task):
    row = [r for r in db["tasks"]["rows"] if r["id"] == task][0]
    return {"tasks.bucket_id": row["bucket_id"], "tasks.done": row["done"]}


def stored_024(db, task, project):
    boards = [v["id"] for v in db["project_views"]["rows"] if v["project_id"] == project and v["view_kind"] == 3]
    rows = [r for r in db["task_buckets"]["rows"] if r["task_id"] == task and r["project_view_id"] in boards]
    task_row = [r for r in db["tasks"]["rows"] if r["id"] == task][0]
    return {"task_buckets.bucket_id (board view)": rows[0]["bucket_id"] if len(rows) == 1 else None,
            "board_view_ids": boards, "tasks.done": task_row["done"]}


def observe_old_workflow(gate, secrets, setup, version_is_024, tag):
    """The sealed old workflow as member1, then the stored state from the SQLite file."""
    watch = lib.HoldWatch()
    rec = lib.Recorder(BASE)
    queries = Q_024 if version_is_024 else Q_023
    db_before = read_db(tag + "-before", queries)
    member = login(rec, "old workflow step 1: POST /api/v1/login", "member1", secrets["member1"])
    body = old_workflow_body(setup["project"], setup["done_bucket"])
    status, parsed, text = rec.call("old workflow step 2: update the task with bucket_id = Done column",
                                    "POST", "/api/v1/tasks/%d" % setup["task"], body=body, headers=member)
    db_after = read_db(tag + "-after", queries, settle=3)
    if version_is_024:
        stored = stored_024(db_after, setup["task"], setup["project"])
        right = {"task_buckets.bucket_id (board view)": setup["done_bucket"], "tasks.done": 1}
        equal = (stored["task_buckets.bucket_id (board view)"] == setup["done_bucket"]
                 and stored["tasks.done"] == 1)
    else:
        stored = stored_023(db_after, setup["task"])
        right = {"tasks.bucket_id": setup["done_bucket"], "tasks.done": 1}
        equal = stored == right
    owner = login(rec, "second witness: owner logs in", "owner1", secrets["owner1"])
    _, witness, _ = rec.call("second witness: owner reads the task", "GET",
                             "/api/v1/tasks/%d" % setup["task"], headers=owner, excerpt=300)
    return {
        "gate": gate, "acting_user": "member1 (project member, right 1 = read and write)",
        "calls": rec.calls,
        "application_answer": {"status": status, "body_excerpt": text[:700]},
        "reported_success": status == 200, "success_criterion": "HTTP 200",
        "db_before": db_before, "db_after": db_after,
        "stored_value": stored, "right_value": right, "stored_equals_right": equal,
        "second_witness_owner_get": {k: witness.get(k) for k in ("id", "title", "done", "bucket_id", "project_id")}
        if isinstance(witness, dict) else None,
        "hold": watch.record(),
    }


def observe_correct_path(secrets, setup, tag):
    """Gate C: the move endpoint of 0.24.0, as member1, on the second task."""
    watch = lib.HoldWatch()
    rec = lib.Recorder(BASE)
    member = login(rec, "POST /api/v1/login", "member1", secrets["member1"])
    _, views, _ = rec.call("member reads the project views to find the board", "GET",
                           "/api/v1/projects/%d/views" % setup["project"], headers=member, excerpt=400)
    board = [v for v in views if v["view_kind"] == "kanban"][0]["id"]
    status, parsed, text = rec.call(
        "correct path as sealed: move the task into the Done column", "POST",
        "/api/v1/projects/%d/views/%d/buckets/%d/tasks" % (setup["project"], board, setup["done_bucket"]),
        body={"task_id": setup["task2"]}, headers=member)
    db_after = read_db(tag + "-after", Q_024, settle=3)
    stored = stored_024(db_after, setup["task2"], setup["project"])
    right = {"task_buckets.bucket_id (board view)": setup["done_bucket"], "tasks.done": 1}
    equal = stored["task_buckets.bucket_id (board view)"] == setup["done_bucket"] and stored["tasks.done"] == 1
    return {
        "gate": "C", "acting_user": "member1 (project member, right 1 = read and write)",
        "case_data": "second task (%s) of the same project" % TASK2_TITLE,
        "calls": rec.calls,
        "application_answer": {"status": status, "body_excerpt": text[:700]},
        "reported_success": status in (200, 201),
        "db_after": db_after, "stored_value": stored, "right_value": right, "stored_equals_right": equal,
        "hold": watch.record(),
    }


def new_secrets():
    return {"jwt": lib.new_secret(24), "owner1": lib.new_secret(12), "member1": lib.new_secret(12)}


def make_repeat(kind, pins):
    def run(repeat):
        secrets = new_secrets()
        lib.log("N5 %s repeat %d" % (kind, repeat))
        evidence = {"repeat": repeat, "kind": kind, "started_utc": lib.utc_now(), "observations": []}
        if kind == "fresh-0.24.0":
            evidence["instances"] = [start(pins, TO_REF, secrets["jwt"], first=True)]
            setup = set_up_024_fresh(secrets)
            evidence["setup"] = setup
            evidence["observations"].append(observe_old_workflow(
                "B-fresh-install", secrets, setup, True, "fresh-%d" % repeat))
        else:
            evidence["instances"] = [start(pins, FROM_REF, secrets["jwt"], first=True)]
            setup = set_up_023(secrets)
            evidence["setup"] = setup
            if kind == "from":
                evidence["observations"].append(observe_old_workflow(
                    "A", secrets, setup, False, "from-%d" % repeat))
            else:
                evidence["db_on_0.23.0_before_upgrade"] = read_db("pre-%d" % repeat, Q_023)
                stop_app()
                lib.wait_hold()
                evidence["instances"].append(start(pins, TO_REF, secrets["jwt"], first=False))
                evidence["upgrade"] = "0.23.0 container stopped and removed; 0.24.0 started on the same data volume"
                evidence["observations"].append(observe_old_workflow(
                    "B", secrets, setup, True, "to-%d" % repeat))
                evidence["observations"].append(observe_correct_path(secrets, setup, "to-c-%d" % repeat))
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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--reuse", action="store_true",
                        help="keep repeats already recorded in the scratch directory and run only the missing ones")
    parser.add_argument("--out", default=os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                      "..", "..", "results", "N5.json"))
    args = parser.parse_args()
    sealed = lib.sealed_case(CASE)
    scratch = lib.scratch_dir(CASE)
    started = lib.utc_now()
    lib.wait_hold()
    lib.teardown(CASE)
    pins, images = lib.pin_images(sealed, ((FROM_REF, REPO), (TO_REF, REPO)))

    runs, reused = {}, []
    for kind in ("from", "to", "fresh-0.24.0"):
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
    fresh = pick(runs["fresh-0.24.0"], "B-fresh-install")
    disposition, summary = classify(a, b, c)
    predicted = sealed["predicted_disposition"]

    def short(obs):
        return [{"repeat": i + 1, "status": o["application_answer"]["status"],
                 "stored_value": o["stored_value"], "right_value": o["right_value"],
                 "stored_equals_right": o["stored_equals_right"]} for i, o in enumerate(obs)]

    result = {
        "schema": "gammatron-real-upgrade-screen-result/v1",
        "case_id": CASE, "screen_lane": "iu1-b",
        "app": sealed["app"], "from_version": sealed["from_version"], "to_version": sealed["to_version"],
        "images": images,
        "conditions": {
            "host": "macOS on Apple Silicon, Docker Desktop, linux/arm64 containers, port bound to 127.0.0.1",
            "install": "gates B and C: IN-PLACE UPGRADE, as the sealed list prescribes for this case "
                       "(0.23.0 on an empty volume, set-up, stop, 0.24.0 on the same volume). "
                       "Gate A: fresh 0.23.0. Supplementary block: fresh install of 0.24.0.",
            "database": "SQLite file in a labelled Docker volume; read from a copy taken with docker cp",
            "time_zone": "VIKUNJA_SERVICE_TIMEZONE=UTC",
            "acting_role": "member1, a second registered user whom the project owner gave right 1 (read and write)",
            "settings_that_matter": "defaults; mailer off; registration open (default) and used for set-up",
        },
        "sealed": {
            "old_workflow_steps": sealed["old_workflow_steps"],
            "correct_path_on_to_version": sealed["correct_path_on_to_version"],
            "database_outcome": sealed["database_outcome"],
            "prediction_condition": sealed["prediction_condition"],
            "predicted_disposition": predicted, "prediction_detail": sealed["prediction_detail"],
        },
        "requests_as_run": {
            "old_workflow": "POST /api/v1/login {username, password}; then POST /api/v1/tasks/{T} with "
                            "{\"title\": \"Ship order 1042\", \"description\": \"\", \"done\": false, "
                            "\"project_id\": P, \"bucket_id\": D}; HTTP 200 is success. The workflow does "
                            "not read the column list first.",
            "correct_path": "POST /api/v1/projects/{P}/views/{V}/buckets/{D}/tasks with {\"task_id\": T2}",
        },
        "gates": {
            "A": {"what": "old workflow on 0.23.0", "pass": summary["gate_A_pass"], "observations_in_short": short(a)},
            "B": {"what": "identical steps on 0.24.0 after an in-place upgrade",
                  "per_repeat": summary["gate_B_per_repeat"], "observations_in_short": short(b)},
            "C": {"what": "correct path on 0.24.0, second task", "pass": summary["gate_C_pass"],
                  "observations_in_short": short(c)},
        },
        "disposition": disposition,
        "disposition_rule": "protocol README table, applied mechanically to gates A, B and C",
        "prediction": {"sealed": predicted, "observed": disposition, "right": predicted == disposition},
        "supplementary_fresh_install_of_to_version": {
            "what": "the same old workflow on a fresh install of 0.24.0, set up through 0.24.0's own API; "
                    "D is that instance's Done column. Not used for the disposition.",
            "observations_in_short": short(fresh),
        },
        "deviations": [],
        "flags": [],
        "repeats_taken_from_an_earlier_execution_of_this_script": reused,
        "repeats": runs,
        "times_utc": {"started": started, "finished": lib.utc_now(), "clock": "date -u on the host"},
        "free_disk_gib_at_end": lib.free_disk_gib(),
    }
    lib.write_json(args.out, result)
    lib.teardown(CASE)
    print(disposition, summary, "fresh:", [(o["application_answer"]["status"], o["stored_equals_right"]) for o in fresh])


if __name__ == "__main__":
    main()

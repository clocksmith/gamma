#!/usr/bin/env python3
"""N4: OpenProject 15.3.0 -> 15.4.0, manual scheduling becomes the default for new work packages.

One repeat against a freshly brought-up pair (../../../bringup/openproject-up.sh 15.3.0-slim 15.4.0-slim).
Set-up, the sealed old workflow (gate A on the old release, gate B on the new one), the correct path
(gate C on the new release, separate work packages) and the database reads. Writes raw evidence only;
`assemble.py` derives the disposition.

  SCREEN_OUT_DIR=<dir> SCREEN_HOLD_FILE=<marker> ./run_case.py <repeat number>
"""
import base64
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import screenlib as lib  # noqa: E402

PG_CONTAINER = "gammatron-op-pg15"
ROLE = "Stage2AuthorRole"
ACTING_USER = "stage2_author"
A_DATES = ("2026-03-02", "2026-03-04")  # sealed fixture: A starts Monday 2026-03-02, finishes Wednesday 2026-03-04
B_BODY = {"subject": "B", "startDate": "2026-03-02", "dueDate": "2026-03-03"}  # sealed step 1, verbatim
RIGHT_START = "2026-03-05"
RIGHT_DUE_ON_FROM_VERSION = "2026-03-06"
# Fixed on a development instance before the counted repeats (see README.md); the environment overrides exist
# only for that development run.
CORRECT_PATH = os.environ.get("N4_CORRECT_PATH", "create-automatic")  # or "patch-automatic"
WITH_CORRECTED_VARIANT = os.environ.get("N4_WITH_CORRECTED", "1") == "1"


def sql_rows(rec, events, label, database, sql):
    wrapped = f"SELECT row_to_json(t) FROM ({sql}) t"
    done = rec.command(events, label, ["docker", "exec", PG_CONTAINER, "psql", "-U", "opqual", "-d", database,
                                       "-At", "-c", wrapped],
                       shown=f"docker exec {PG_CONTAINER} psql -U opqual -d {database} -At -c \"{wrapped}\"")
    return [json.loads(line) for line in done.stdout.splitlines() if line.strip().startswith("{")]


def grant_relations_permission(rec, events, container):
    ruby = (f"r = Role.find_by!(name: '{ROLE}'); r.add_permission!(:manage_work_package_relations); "
            "puts 'ROLE_PERMISSIONS:' + r.reload.permissions.map(&:to_s).sort.join(',')")
    rec.command(events, f"grant manage_work_package_relations to {ROLE}",
                ["docker", "exec", container, "bundle", "exec", "rails", "runner", ruby])


def gate(rec, release, database, label, correct_path, is_from_version, with_from=False):
    """A is created as set-up; then the two sealed workflow requests; then the database reads.

    `correct_path` is None for the old workflow, or one of the two forms the sealed list gives for the correct
    path. `with_from` adds `_links.from` (B itself) to the relation request (see README.md, deviation)."""
    events = []
    gaps_before = rec.gaps()
    base = release["url"]
    auth = {"Authorization": "Basic " + base64.b64encode(("apikey:" + release["seed"]["authorToken"]).encode()).decode()}
    note = f"API token of {ACTING_USER}"
    project = release["seed"]["projectId"]
    made_a = rec.http(events, "set-up: create work package A", "POST", base,
                      f"/api/v3/projects/{project}/work_packages", auth, note,
                      {"subject": f"A ({label})", "startDate": A_DATES[0], "dueDate": A_DATES[1]})
    a_id = made_a["json"].get("id") if isinstance(made_a["json"], dict) else None
    b_body = dict(B_BODY)
    if correct_path == "create-automatic":
        b_body["scheduleManually"] = False
    made_b = rec.http(events, "workflow step 1: create work package B", "POST", base,
                      f"/api/v3/projects/{project}/work_packages", auth, note, b_body)
    b_id = made_b["json"].get("id") if isinstance(made_b["json"], dict) else None
    wp_sql = ("SELECT id, subject, start_date, due_date, duration, schedule_manually, ignore_non_working_days, "
              f"lock_version FROM work_packages WHERE id IN ({a_id or 0}, {b_id or 0}) ORDER BY id")
    before = sql_rows(rec, events, "database read after step 1, before step 2: work packages", database, wp_sql)
    relation_body = {"type": "follows", "_links": {"to": {"href": f"/api/v3/work_packages/{a_id}"}}}
    if with_from:
        relation_body["_links"]["from"] = {"href": f"/api/v3/work_packages/{b_id}"}
    made_rel = rec.http(events, "workflow step 2: POST relation B follows A", "POST", base,
                        f"/api/v3/work_packages/{b_id}/relations", auth, note, relation_body)
    statuses = [made_b["status"], made_rel["status"]]
    requests = [{"method": "POST", "path": f"/api/v3/projects/{project}/work_packages", "body": b_body},
                {"method": "POST", "path": f"/api/v3/work_packages/{b_id}/relations", "body": relation_body}]
    if correct_path == "patch-automatic":
        # The sealed correct path's second form: switch B to automatic scheduling once the relation exists.
        got = rec.http(events, "correct path: GET B, read lockVersion", "GET", base,
                       f"/api/v3/work_packages/{b_id}", auth, note)
        lock = got["json"].get("lockVersion") if isinstance(got["json"], dict) else None
        patch_body = {"lockVersion": lock, "scheduleManually": False}
        patched = rec.http(events, "correct path: PATCH scheduleManually false onto B", "PATCH", base,
                           f"/api/v3/work_packages/{b_id}", auth, note, patch_body)
        statuses.append(patched["status"])
        requests.append({"method": "PATCH", "path": f"/api/v3/work_packages/{b_id}", "body": patch_body})
    relations = sql_rows(rec, events, "database read after the workflow: relations", database,
                         f"SELECT * FROM relations WHERE from_id = {b_id or 0} OR to_id = {b_id or 0} ORDER BY id")
    after = sql_rows(rec, events, "database read after the workflow: work packages", database, wp_sql)
    b_row = next((r for r in after if r["id"] == b_id), None) or {}
    right = {"b_start_date": RIGHT_START}
    ok = b_row.get("start_date") == RIGHT_START
    if is_from_version:
        right.update({"b_schedule_manually": False, "b_due_date": RIGHT_DUE_ON_FROM_VERSION})
        ok = ok and b_row.get("schedule_manually") is False and b_row.get("due_date") == RIGHT_DUE_ON_FROM_VERSION
    return {
        "release_tag": release["tag"], "database": database, "work_package_ids": {"A": a_id, "B": b_id},
        "workflow_requests": requests,
        "workflow_response_status": statuses,
        "reported_success": statuses[:2] == [201, 201] and all(s in (200, 201) for s in statuses),
        "stored": {"relation_rows": len(relations), "b_schedule_manually": b_row.get("schedule_manually"),
                   "b_start_date": b_row.get("start_date"), "b_due_date": b_row.get("due_date")},
        "right": right, "stored_is_right": bool(ok),
        "work_packages_before_relation": before, "work_packages_after": after, "relations_after": relations,
        "overlapped_hold": lib.overlapped_hold(events, gaps_before, rec.gaps()),
        "events": events,
    }


def main():
    repeat = int(sys.argv[1])
    out_dir = os.environ["SCREEN_OUT_DIR"]
    waited = lib.wait_for_no_hold()
    state = lib.load_state("openproject.json")
    rec = lib.Recorder()
    result = {
        "case": "N4", "repeat": repeat, "started_utc": lib.utc_now(), "waited_for_hold_seconds": waited,
        "images": lib.image_pins([f"openproject/openproject:{state['old']['tag']}",
                                  f"openproject/openproject:{state['new']['tag']}", "postgres:15"]),
        "setup": {"events": []},
    }
    setup = result["setup"]["events"]
    for side, database in (("old", "op_old_qual"), ("new", "op_new_qual")):
        grant_relations_permission(rec, setup, state[side]["container"])
        sql_rows(rec, setup, f"{side}: column default of work_packages.schedule_manually, working days, role", database,
                 "SELECT (SELECT column_default FROM information_schema.columns WHERE table_name = 'work_packages' "
                 "AND column_name = 'schedule_manually') AS schedule_manually_column_default, "
                 "(SELECT value FROM settings WHERE name = 'working_days') AS working_days_setting, "
                 "(SELECT string_agg(permission, ',' ORDER BY permission) FROM role_permissions rp JOIN roles r "
                 f"ON r.id = rp.role_id WHERE r.name = '{ROLE}') AS role_permissions, "
                 "(SELECT count(*) FROM non_working_days) AS non_working_day_rows")
    result["correct_path_form"] = CORRECT_PATH
    variants = [("as sealed", result, False)]
    if WITH_CORRECTED_VARIANT:
        result["corrected"] = {}
        variants.append(("corrected", result["corrected"], True))
    for name, gates, with_from in variants:
        lib.wait_for_no_hold()
        gates["gate_A"] = gate(rec, state["old"], "op_old_qual", f"gate A {name}", None, True, with_from)
        lib.wait_for_no_hold()
        gates["gate_B"] = gate(rec, state["new"], "op_new_qual", f"gate B {name}", None, False, with_from)
        lib.wait_for_no_hold()
        gates["gate_C"] = gate(rec, state["new"], "op_new_qual", f"gate C {name}", CORRECT_PATH, False, with_from)
    result["process_stopped_gaps"] = rec.gaps()
    result["finished_utc"] = lib.utc_now()
    lib.write_json(os.path.join(out_dir, f"repeat-{repeat}.json"), result)
    for name, gates, _ in variants:
        for g in ("gate_A", "gate_B", "gate_C"):
            r = gates[g]
            print(name, g, r["release_tag"], "status", r["workflow_response_status"], "stored", r["stored"],
                  "right" if r["stored_is_right"] else "NOT right", "hold-overlap" if r["overlapped_hold"] else "")


if __name__ == "__main__":
    main()

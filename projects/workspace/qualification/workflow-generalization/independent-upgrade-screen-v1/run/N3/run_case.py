#!/usr/bin/env python3
"""N3: OpenProject 13.4.0 -> 14.0.0, relation attribute `delay` renamed `lag`.

One repeat against a freshly brought-up pair (../../../bringup/openproject-up.sh 13.4.0-slim 14.0.0-slim).
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
FIXTURE_DATE = "2026-03-02"  # sealed fixture: A and B both start and finish on Monday 2026-03-02
RIGHT_START = "2026-03-06"   # sealed right value for B's start date
RIGHT_GAP = 3                # sealed right value for relations.delay (old) / relations.lag (new)


def sql_rows(rec, events, label, database, sql):
    """Read rows as JSON straight from PostgreSQL in the database container."""
    wrapped = f"SELECT row_to_json(t) FROM ({sql}) t"
    done = rec.command(events, label, ["docker", "exec", PG_CONTAINER, "psql", "-U", "opqual", "-d", database,
                                       "-At", "-c", wrapped],
                       shown=f"docker exec {PG_CONTAINER} psql -U opqual -d {database} -At -c \"{wrapped}\"")
    return [json.loads(line) for line in done.stdout.splitlines() if line.strip().startswith("{")]


def grant_relations_permission(rec, events, container):
    """Set-up: give the acting role manage_work_package_relations, through the application's own role model
    (the same means the frozen seeder uses to define the role)."""
    ruby = (f"r = Role.find_by!(name: '{ROLE}'); r.add_permission!(:manage_work_package_relations); "
            "puts 'ROLE_PERMISSIONS:' + r.reload.permissions.map(&:to_s).sort.join(',')")
    rec.command(events, f"grant manage_work_package_relations to {ROLE}",
                ["docker", "exec", container, "bundle", "exec", "rails", "runner", ruby])


def gate(rec, release, database, gap_column, gap_property, label, with_from=False):
    """Create A and B as the acting user, send the relation request with `gap_property`: 3, read the database.

    `with_from` adds `_links.from` (B itself) to the request: the smallest correction, see README.md."""
    events = []
    gaps_before = rec.gaps()
    base = release["url"]
    auth = {"Authorization": "Basic " + base64.b64encode(("apikey:" + release["seed"]["authorToken"]).encode()).decode()}
    note = f"API token of {ACTING_USER}"
    project = release["seed"]["projectId"]
    ids = {}
    for name in ("A", "B"):
        made = rec.http(events, f"set-up: create work package {name}", "POST", base,
                        f"/api/v3/projects/{project}/work_packages", auth, note,
                        {"subject": f"N3 {label} task {name}", "startDate": FIXTURE_DATE, "dueDate": FIXTURE_DATE})
        ids[name] = made["json"].get("id") if isinstance(made["json"], dict) else None
    wp_sql = ("SELECT id, subject, start_date, due_date, duration, schedule_manually, ignore_non_working_days, "
              f"lock_version FROM work_packages WHERE id IN ({ids['A'] or 0}, {ids['B'] or 0}) ORDER BY id")
    before = sql_rows(rec, events, "database read before the workflow: work packages", database, wp_sql)
    request_body = {"type": "follows", gap_property: 3,
                    "_links": {"to": {"href": f"/api/v3/work_packages/{ids['A']}"}}}
    if with_from:
        request_body["_links"]["from"] = {"href": f"/api/v3/work_packages/{ids['B']}"}
    status = rec.http(events, f"workflow: POST relation with {gap_property}", "POST", base,
                      f"/api/v3/work_packages/{ids['B']}/relations", auth, note, request_body)["status"]
    rel_sql = f"SELECT * FROM relations WHERE from_id = {ids['B'] or 0} OR to_id = {ids['B'] or 0} ORDER BY id"
    relations = sql_rows(rec, events, "database read after the workflow: relations", database, rel_sql)
    after = sql_rows(rec, events, "database read after the workflow: work packages", database, wp_sql)
    b_row = next((r for r in after if r["id"] == ids["B"]), None)
    return {
        "release_tag": release["tag"], "database": database, "work_package_ids": ids,
        "workflow_request": {"method": "POST", "path": f"/api/v3/work_packages/{ids['B']}/relations",
                             "body": request_body},
        "workflow_response_status": status,
        "reported_success": status == 201,
        "stored": {
            "relation_rows": len(relations),
            gap_column: relations[0].get(gap_column) if relations else None,
            "b_start_date": b_row["start_date"] if b_row else None,
            "b_due_date": b_row["due_date"] if b_row else None,
        },
        "right": {gap_column: RIGHT_GAP, "b_start_date": RIGHT_START},
        "stored_is_right": bool(relations) and relations[0].get(gap_column) == RIGHT_GAP
                           and b_row is not None and b_row["start_date"] == RIGHT_START,
        "work_packages_before": before, "work_packages_after": after, "relations_after": relations,
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
        "case": "N3", "repeat": repeat, "started_utc": lib.utc_now(), "waited_for_hold_seconds": waited,
        "images": lib.image_pins([f"openproject/openproject:{state['old']['tag']}",
                                  f"openproject/openproject:{state['new']['tag']}", "postgres:15"]),
        "setup": {"events": []},
    }
    setup = result["setup"]["events"]
    for side, database in (("old", "op_old_qual"), ("new", "op_new_qual")):
        grant_relations_permission(rec, setup, state[side]["container"])
        lib_rows = sql_rows(rec, setup, f"{side}: relations table columns", database,
                            "SELECT column_name FROM information_schema.columns WHERE table_name = 'relations' "
                            "ORDER BY ordinal_position")
        result["setup"][f"{side}_relations_columns"] = [r["column_name"] for r in lib_rows]
        sql_rows(rec, setup, f"{side}: working days, role permission, acting member", database,
                 "SELECT (SELECT value FROM settings WHERE name = 'working_days') AS working_days_setting, "
                 "(SELECT string_agg(permission, ',' ORDER BY permission) FROM role_permissions rp JOIN roles r "
                 f"ON r.id = rp.role_id WHERE r.name = '{ROLE}') AS role_permissions, "
                 "(SELECT count(*) FROM non_working_days) AS non_working_day_rows")

    # The steps exactly as the sealed list writes them.
    lib.wait_for_no_hold()
    result["gate_A"] = gate(rec, state["old"], "op_old_qual", "delay", "delay", "gate A as sealed")
    lib.wait_for_no_hold()
    result["gate_B"] = gate(rec, state["new"], "op_new_qual", "lag", "delay", "gate B as sealed")
    lib.wait_for_no_hold()
    result["gate_C"] = gate(rec, state["new"], "op_new_qual", "lag", "lag", "gate C as sealed")
    # The same steps with the smallest correction (`_links.from` added), on separate work packages.
    corrected = result["corrected"] = {}
    lib.wait_for_no_hold()
    corrected["gate_A"] = gate(rec, state["old"], "op_old_qual", "delay", "delay", "gate A corrected", with_from=True)
    lib.wait_for_no_hold()
    corrected["gate_B"] = gate(rec, state["new"], "op_new_qual", "lag", "delay", "gate B corrected", with_from=True)
    lib.wait_for_no_hold()
    corrected["gate_C"] = gate(rec, state["new"], "op_new_qual", "lag", "lag", "gate C corrected", with_from=True)
    result["process_stopped_gaps"] = rec.gaps()
    result["finished_utc"] = lib.utc_now()
    lib.write_json(os.path.join(out_dir, f"repeat-{repeat}.json"), result)
    for name, gates in (("as sealed", result), ("corrected", corrected)):
        for g in ("gate_A", "gate_B", "gate_C"):
            r = gates[g]
            print(name, g, r["release_tag"], "status", r["workflow_response_status"], "stored", r["stored"],
                  "right" if r["stored_is_right"] else "NOT right", "hold-overlap" if r["overlapped_hold"] else "")


if __name__ == "__main__":
    main()

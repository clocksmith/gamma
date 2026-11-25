#!/usr/bin/env python3
"""L1: OpenProject 17.7.0 -> 17.8.0, single `version` link replaced by `targetVersions`.

One repeat against a freshly brought-up pair (../../../screening/openproject-up.sh 17.7.0-slim 17.8.0-slim,
the byte-identical copy of the frozen bring-up that mounts the screening seeder; the sealed list names it).
Set-up, the sealed old workflow (gate A on the old release, gate B on the new one), the correct path
(gate C on the new release, a separate work package) and the database reads. Writes raw evidence only;
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
WITNESS_USER = "stage2_approver"
VERSION_NAME = "Sprint 3"
SETUP_RUBY = (
    f"r = Role.find_by!(name: '{ROLE}'); r.add_permission!(:assign_versions); "
    "p = Project.find_by!(identifier: 'stage2-qual-proj'); "
    f"v = Version.find_or_create_by!(project: p, name: '{VERSION_NAME}'); "
    "a = (Setting.work_package_multiple_versions? rescue \"unavailable: #{$!.class}\"); "
    "b = (Setting::WorkPackageMultipleVersions.active? rescue \"unavailable: #{$!.class}\"); "
    "puts 'L1_SETUP_JSON:' + {version_id: v.id, version_name: v.name, version_status: v.status, "
    "version_sharing: v.sharing, role_permissions: r.reload.permissions.map(&:to_s).sort, "
    "setting_work_package_multiple_versions: a, setting_class_active: b, "
    "core_version: OpenProject::VERSION.to_s}.to_json"
)


def sql_rows(rec, events, label, database, sql):
    wrapped = f"SELECT row_to_json(t) FROM ({sql}) t"
    done = rec.command(events, label, ["docker", "exec", PG_CONTAINER, "psql", "-U", "opqual", "-d", database,
                                       "-At", "-c", wrapped],
                       shown=f"docker exec {PG_CONTAINER} psql -U opqual -d {database} -At -c \"{wrapped}\"")
    return [json.loads(line) for line in done.stdout.splitlines() if line.strip().startswith("{")]


def setup_side(rec, events, container):
    done = rec.command(events, f"grant assign_versions to {ROLE}, create version '{VERSION_NAME}', read the setting",
                       ["docker", "exec", container, "bundle", "exec", "rails", "runner", SETUP_RUBY])
    for line in done.stdout.splitlines():
        if line.startswith("L1_SETUP_JSON:"):
            return json.loads(line[len("L1_SETUP_JSON:"):])
    return {}


def token_auth(token):
    return {"Authorization": "Basic " + base64.b64encode(("apikey:" + token).encode()).decode()}


def read_stored(rec, events, database, w_id, has_join_table, when):
    wp = sql_rows(rec, events, f"database read {when}: work package", database,
                  "SELECT w.id, w.subject, to_jsonb(w)->'version_id' AS version_id, w.lock_version, "
                  "(SELECT count(*) FROM journals j WHERE j.journable_type = 'WorkPackage' AND j.journable_id = w.id) "
                  f"AS journal_count FROM work_packages w WHERE w.id = {w_id or 0}")
    joined = []
    if has_join_table:
        joined = sql_rows(rec, events, f"database read {when}: work_package_versions", database,
                          f"SELECT * FROM work_package_versions WHERE work_package_id = {w_id or 0} ORDER BY id")
    return {"work_package": wp[0] if wp else None, "work_package_versions": joined}


def gate(rec, release, database, version_id, label, link_property, is_from_version, has_join_table):
    events = []
    gaps_before = rec.gaps()
    base = release["url"]
    actor, note = token_auth(release["seed"]["authorToken"]), f"API token of {ACTING_USER}"
    project = release["seed"]["projectId"]
    made = rec.http(events, "set-up: create work package W", "POST", base,
                    f"/api/v3/projects/{project}/work_packages", actor, note, {"subject": f"W ({label})"})
    w_id = made["json"].get("id") if isinstance(made["json"], dict) else None
    before = read_stored(rec, events, database, w_id, has_join_table, "before the workflow")
    got = rec.http(events, "workflow step 1: GET the work package, read lockVersion", "GET", base,
                   f"/api/v3/work_packages/{w_id}", actor, note)
    lock = got["json"].get("lockVersion") if isinstance(got["json"], dict) else None
    href = f"/api/v3/versions/{version_id}"
    links = {"version": {"href": href}} if link_property == "version" else {"targetVersions": [{"href": href}]}
    body = {"lockVersion": lock, "_links": links}
    patched = rec.http(events, f"workflow step 2: PATCH with _links.{link_property}", "PATCH", base,
                       f"/api/v3/work_packages/{w_id}", actor, note, body)
    after = read_stored(rec, events, database, w_id, has_join_table, "after the workflow")
    seen = rec.http(events, "second witness: GET the work package with another account", "GET", base,
                    f"/api/v3/work_packages/{w_id}", token_auth(release["seed"]["approverToken"]),
                    f"API token of {WITNESS_USER}")
    witness_links = (seen["json"] or {}).get("_links", {}) if isinstance(seen["json"], dict) else {}
    row = after["work_package"] or {}
    rows = after["work_package_versions"]
    if is_from_version:
        right = {"work_packages.version_id": version_id}
        ok = row.get("version_id") == version_id
    else:
        right = {"work_package_versions": [{"work_package_id": w_id, "version_id": version_id, "kind": "target"}]}
        ok = (len(rows) == 1 and rows[0].get("work_package_id") == w_id and rows[0].get("version_id") == version_id
              and rows[0].get("kind") == "target")
    return {
        "release_tag": release["tag"], "database": database, "work_package_id": w_id, "version_id": version_id,
        "workflow_requests": [{"method": "GET", "path": f"/api/v3/work_packages/{w_id}"},
                              {"method": "PATCH", "path": f"/api/v3/work_packages/{w_id}", "body": body}],
        "workflow_response_status": patched["status"],
        "reported_success": patched["status"] == 200,
        "stored": {"work_packages.version_id": row.get("version_id"),
                   "work_package_versions": [{k: r.get(k) for k in ("work_package_id", "version_id", "kind")} for r in rows],
                   "lock_version_before": (before["work_package"] or {}).get("lock_version"),
                   "lock_version_after": row.get("lock_version"),
                   "journal_count_before": (before["work_package"] or {}).get("journal_count"),
                   "journal_count_after": row.get("journal_count")},
        "right": right, "stored_is_right": bool(ok),
        "second_witness": {"account": WITNESS_USER, "status": seen["status"],
                           "_links.version": witness_links.get("version"),
                           "_links.targetVersions": witness_links.get("targetVersions")},
        "database_before": before, "database_after": after,
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
        "case": "L1", "repeat": repeat, "started_utc": lib.utc_now(), "waited_for_hold_seconds": waited,
        "images": lib.image_pins([f"openproject/openproject:{state['old']['tag']}",
                                  f"openproject/openproject:{state['new']['tag']}", "postgres:15"]),
        "setup": {"events": []},
    }
    setup = result["setup"]["events"]
    info, join_table = {}, {}
    for side, database in (("old", "op_old_qual"), ("new", "op_new_qual")):
        info[side] = setup_side(rec, setup, state[side]["container"])
        rows = sql_rows(rec, setup, f"{side}: stored setting and whether work_package_versions exists", database,
                        "SELECT (SELECT value FROM settings WHERE name = 'work_package_multiple_versions') AS setting_row_value, "
                        "(SELECT count(*) FROM information_schema.tables WHERE table_name = 'work_package_versions') AS join_table, "
                        "(SELECT count(*) FROM information_schema.columns WHERE table_name = 'work_packages' "
                        "AND column_name = 'version_id') AS version_id_column")
        join_table[side] = bool(rows and rows[0]["join_table"])
        info[side]["database"] = rows[0] if rows else None
    result["setup"]["sides"] = info
    lib.wait_for_no_hold()
    result["gate_A"] = gate(rec, state["old"], "op_old_qual", info["old"].get("version_id"), "gate A", "version",
                            True, join_table["old"])
    lib.wait_for_no_hold()
    result["gate_B"] = gate(rec, state["new"], "op_new_qual", info["new"].get("version_id"), "gate B", "version",
                            False, join_table["new"])
    lib.wait_for_no_hold()
    result["gate_C"] = gate(rec, state["new"], "op_new_qual", info["new"].get("version_id"), "gate C",
                            "targetVersions", False, join_table["new"])
    result["process_stopped_gaps"] = rec.gaps()
    result["finished_utc"] = lib.utc_now()
    lib.write_json(os.path.join(out_dir, f"repeat-{repeat}.json"), result)
    for g in ("gate_A", "gate_B", "gate_C"):
        r = result[g]
        print(g, r["release_tag"], "status", r["workflow_response_status"], "stored", r["stored"],
              "right" if r["stored_is_right"] else "NOT right", "hold-overlap" if r["overlapped_hold"] else "")


if __name__ == "__main__":
    main()

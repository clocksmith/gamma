#!/usr/bin/env python3
"""L2: NetBox v4.0.11 -> v4.1.0, creating a VLAN group limited to VLAN IDs 100..199.

One command runs gates A, B and C, three repeats each, every repeat on a stack started
from nothing, and writes ../../results/L2.json:

    SCREEN_SCRATCH=/some/dir [SCREEN_HOLD_FILE=/path/HOLD] python3 run.py

The from-version repeats and the to-version repeats run side by side on two ports to
save wall-clock time; they share nothing. The old workflow's request, the correct path
and the right value come from the sealed list (screen-list.json, case L2).
"""
import argparse
import concurrent.futures
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib  # noqa: E402
import netbox  # noqa: E402

CASE = "L2"
FROM_REF, TO_REF = "netboxcommunity/netbox:v4.0.11", "netboxcommunity/netbox:v4.1.0"
PORTS = {"from": 28640, "to": 28641}
PERMISSIONS = [("engineer-vlan-groups", ["ipam.vlangroup"], ["view", "add", "change"])]

OLD_WORKFLOW_BODY = {"name": "campus-a", "slug": "campus-a", "min_vid": 100, "max_vid": 199}   # sealed
# Gate C runs on the instance that served gate B, on a second group.
CORRECT_PATH_BODY = {"name": "campus-c", "slug": "campus-c", "vid_ranges": [[100, 199]]}

SQL_FROM = "SELECT id, name, slug, min_vid, max_vid FROM ipam_vlangroup ORDER BY id"
SQL_TO = "SELECT id, name, slug, vid_ranges FROM ipam_vlangroup ORDER BY id"
RIGHT_FROM = {"min_vid": "100", "max_vid": "199"}
RIGHT_TO = {"vid_ranges": '{"[100,200)"}'}
REUSED = []


def row_for(lines, row_id):
    if len(lines) < 2 or row_id is None:
        return None
    header = lines[0].split("|")
    for line in lines[1:]:
        cells = line.split("|")
        if cells[0] == str(row_id):
            return dict(zip(header, cells))
    return None


def set_up(stack):
    rec = lib.Recorder(stack.base)
    stack.create_engineer(rec, PERMISSIONS)
    return {"calls": rec.calls, "engineer_user_id": stack.engineer_user_id,
            "db_rows_engineer": stack.sql("SELECT id, username, is_superuser FROM users_user ORDER BY id")}


def observe(gate, stack, body, description, to_version):
    watch = lib.HoldWatch()
    rec = lib.Recorder(stack.base)
    query = SQL_TO if to_version else SQL_FROM
    right = RIGHT_TO if to_version else RIGHT_FROM
    rows_before = stack.sql(query)
    status, parsed, text = rec.call(description, "POST", "/api/ipam/vlan-groups/", body=body,
                                    headers=stack.engineer)
    new_id = parsed.get("id") if status == 201 and isinstance(parsed, dict) else None
    rows_after = stack.sql(query)
    row = row_for(rows_after, new_id)
    stored = {k: row[k] for k in right} if row else None
    witness, probes = None, []
    if new_id is not None:
        _, got, _ = rec.call("second witness: superuser reads the group", "GET",
                             "/api/ipam/vlan-groups/%d/" % new_id, headers=stack.admin, excerpt=300)
        if isinstance(got, dict):
            witness = {k: got.get(k) for k in ("id", "name", "slug", "min_vid", "max_vid", "vid_ranges") if k in got}
        # After the stored value has been read: does the group take a VLAN outside and inside 100..199?
        for vid in (500, 150):
            p_status, _, p_text = rec.call(
                "supplementary probe after the read: superuser adds VLAN %d to the group" % vid, "POST",
                "/api/ipam/vlans/", body={"vid": vid, "name": "probe-%d-g%d" % (vid, new_id), "group": new_id},
                headers=stack.admin, excerpt=300)
            probes.append({"vid": vid, "status": p_status, "body_excerpt": p_text[:300]})
    return {
        "gate": gate, "acting_user": "neteng (not a superuser; permissions %s)" % [p[0] for p in PERMISSIONS],
        "calls": rec.calls,
        "application_answer": {"status": status, "body_excerpt": text[:700]},
        "reported_success": status == 201, "success_criterion": "HTTP 201",
        "returned_id": new_id,
        "db_query": query, "db_rows_before": rows_before, "db_rows_after": rows_after,
        "stored_value": stored, "right_value": right, "stored_equals_right": stored == right,
        "second_witness_superuser_get": witness,
        "supplementary_probe_after_read": probes,
        "hold": watch.record(),
    }


def make_repeat(kind, pins):
    def run(repeat):
        lib.log("L2 %s repeat %d: bring-up" % (kind, repeat))
        ref = FROM_REF if kind == "from" else TO_REF
        stack = netbox.Stack(CASE + kind[0], PORTS[kind], pins, ref).bring_up()
        setup = set_up(stack)
        evidence = {"repeat": repeat, "image": ref, "pulled_ref": pins[ref]["pulled_ref"],
                    "instance_started_utc": stack.started_utc, "instance_ready_utc": stack.ready_utc,
                    "conditions": stack.conditions(), "setup": setup, "observations": []}
        if kind == "from":
            evidence["observations"].append(observe(
                "A", stack, OLD_WORKFLOW_BODY, "old workflow exactly as sealed, from-version", False))
        else:
            evidence["observations"].append(observe(
                "B", stack, OLD_WORKFLOW_BODY, "old workflow exactly as sealed, to-version", True))
            evidence["observations"].append(observe(
                "C", stack, CORRECT_PATH_BODY, "correct path as sealed, to-version, on a second group", True))
        lib.log("L2 %s repeat %d: done" % (kind, repeat))
        return evidence
    return run


def run_kind(kind, pins, repeats, scratch, reuse):
    out = []
    for i in range(1, repeats + 1):
        path = os.path.join(scratch, "%s-%d.json" % (kind, i))
        if reuse and os.path.exists(path):
            with open(path) as handle:
                out.append(lib.json.load(handle))
            REUSED.append("%s repeat %d" % (kind, i))
            continue
        out.append(lib.run_repeat(CASE + kind[0], make_repeat(kind, pins), i))
        lib.write_json(path, out[-1])
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--reuse", action="store_true",
                        help="keep repeats already recorded in the scratch directory and run only the missing ones")
    parser.add_argument("--out", default=os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                      "..", "..", "results", "L2.json"))
    args = parser.parse_args()
    sealed = lib.sealed_case(CASE)
    scratch = lib.scratch_dir(CASE)
    started = lib.utc_now()
    lib.wait_hold()
    pins, images = lib.pin_images(sealed, ((FROM_REF, netbox.NB_REPO), (TO_REF, netbox.NB_REPO),
                                           (netbox.PG_REF, netbox.PG_REPO), (netbox.REDIS_REF, netbox.REDIS_REPO)))
    with concurrent.futures.ThreadPoolExecutor(2) as pool:
        fut_from = pool.submit(run_kind, "from", pins, args.repeats, scratch, args.reuse)
        fut_to = pool.submit(run_kind, "to", pins, args.repeats, scratch, args.reuse)
        from_repeats, to_repeats = fut_from.result(), fut_to.result()

    def pick(repeats, gate):
        return [o for r in repeats for o in r["observations"] if o["gate"] == gate]

    a, b, c = pick(from_repeats, "A"), pick(to_repeats, "B"), pick(to_repeats, "C")
    disposition, summary = netbox.classify(a, b, c)
    predicted = sealed["predicted_disposition"]

    def short(obs):
        return [{"repeat": i + 1, "status": o["application_answer"]["status"],
                 "body": o["application_answer"]["body_excerpt"][:160],
                 "stored_value": o["stored_value"], "right_value": o["right_value"],
                 "stored_equals_right": o["stored_equals_right"],
                 "probe_vlan_500_status": next((p["status"] for p in o["supplementary_probe_after_read"]
                                                if p["vid"] == 500), None)} for i, o in enumerate(obs)]

    result = {
        "schema": "gammatron-real-upgrade-screen-result/v1",
        "case_id": CASE, "screen_lane": "iu1-b",
        "app": sealed["app"], "from_version": sealed["from_version"], "to_version": sealed["to_version"],
        "images": images,
        "conditions": {
            "host": "macOS on Apple Silicon, Docker Desktop, linux/arm64 containers, ports bound to 127.0.0.1",
            "install": "every repeat is a fresh install on an empty PostgreSQL database; no in-place upgrade was run",
            "time_zone": "container defaults (UTC); the case holds no time value",
            "acting_role": "neteng, a non-superuser created by the superuser through the REST API, with object "
                           "permissions view/add/change on ipam.vlangroup, and its own API token",
            "settings_that_matter": "image defaults; no plugins",
            "gate_B_and_C": "the same to-version instance serves B (group campus-a) and C (group campus-c)",
            "parallelism": "from-version and to-version stacks ran side by side on two ports; they share nothing",
        },
        "sealed": {
            "old_workflow_steps": sealed["old_workflow_steps"],
            "correct_path_on_to_version": sealed["correct_path_on_to_version"],
            "database_outcome": sealed["database_outcome"],
            "predicted_disposition": predicted, "prediction_detail": sealed["prediction_detail"],
        },
        "requests_as_run": {
            "old_workflow": "POST /api/ipam/vlan-groups/ with {\"name\": \"campus-a\", \"slug\": \"campus-a\", "
                            "\"min_vid\": 100, \"max_vid\": 199}, header Authorization: Token <redacted>; "
                            "HTTP 201 is success",
            "correct_path": "POST /api/ipam/vlan-groups/ with {\"name\": \"campus-c\", \"slug\": \"campus-c\", "
                            "\"vid_ranges\": [[100, 199]]}",
            "stored_value_read": "ipam_vlangroup row of the returned id, with psql inside the PostgreSQL container",
        },
        "gates": {
            "A": {"what": "old workflow on the from-version", "pass": summary["gate_A_pass"],
                  "observations_in_short": short(a)},
            "B": {"what": "identical steps on the to-version", "per_repeat": summary["gate_B_per_repeat"],
                  "observations_in_short": short(b)},
            "C": {"what": "correct path on the to-version", "pass": summary["gate_C_pass"],
                  "observations_in_short": short(c)},
        },
        "disposition": disposition,
        "disposition_rule": "protocol README table, applied mechanically to the stored values below; the VLAN "
                            "probes are supplementary and do not enter the rule",
        "prediction": {"sealed": predicted, "observed": disposition, "right": predicted == disposition},
        "deviations": [],
        "flags": [],
        "notes": ["Gate C uses a second group (campus-c) on the instance that served gate B; the request is "
                  "otherwise the sealed correct path.",
                  "After each stored value was read, the superuser tried to add VLAN 500 and VLAN 150 to the "
                  "group, to show what the stored range means for the business outcome."],
        "repeats_taken_from_an_earlier_execution_of_this_script": sorted(REUSED),
        "repeats": {"from_version": from_repeats, "to_version": to_repeats},
        "times_utc": {"started": started, "finished": lib.utc_now(), "clock": "date -u on the host"},
        "free_disk_gib_at_end": lib.free_disk_gib(),
    }
    lib.write_json(args.out, result)
    print(disposition, summary)


if __name__ == "__main__":
    main()

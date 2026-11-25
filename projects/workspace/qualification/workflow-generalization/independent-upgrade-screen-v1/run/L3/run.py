#!/usr/bin/env python3
"""L3: NetBox v4.1.11 -> v4.2.0, registering a prefix at a site through the REST API.

One command runs gates A, B and C, three repeats each, every repeat on a stack started
from nothing, and writes ../../results/L3.json:

    SCREEN_SCRATCH=/some/dir [SCREEN_HOLD_FILE=/path/HOLD] python3 run.py

The from-version repeats and the to-version repeats run side by side on two ports to
save wall-clock time; they share nothing. The old workflow's request, the correct path
and the right value come from the sealed list (screen-list.json, case L3).
"""
import argparse
import concurrent.futures
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib  # noqa: E402
import netbox  # noqa: E402

CASE = "L3"
FROM_REF, TO_REF = "netboxcommunity/netbox:v4.1.11", "netboxcommunity/netbox:v4.2.0"
PORTS = {"from": 28630, "to": 28631}
PREFIX = "192.0.2.0/24"          # sealed
PREFIX_C = "198.51.100.0/24"     # gate C runs on the same to-version instance, on a second prefix

PERMISSIONS = [("engineer-prefixes", ["ipam.prefix"], ["view", "add", "change"]),
               ("engineer-sites-read", ["dcim.site"], ["view"])]


def old_workflow_body(site):
    return {"prefix": PREFIX, "site": site, "status": "active"}


def correct_path_body(site):
    return {"prefix": PREFIX_C, "scope_type": "dcim.site", "scope_id": site, "status": "active"}


SQL_FROM = "SELECT id, prefix, status, site_id FROM ipam_prefix ORDER BY id"
SQL_TO = "SELECT id, prefix, status, scope_type_id, scope_id, _site_id FROM ipam_prefix ORDER BY id"
SQL_CT = "SELECT id, app_label, model FROM django_content_type WHERE app_label = 'dcim' AND model = 'site'"


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
    status, site, text = rec.call("superuser creates site HQ", "POST", "/api/dcim/sites/",
                                  body={"name": "HQ", "slug": "hq"}, headers=stack.admin, excerpt=300)
    if status != 201:
        raise RuntimeError("site: %s %s" % (status, text[:300]))
    stack.create_engineer(rec, PERMISSIONS)
    return {"calls": rec.calls, "site_id": site["id"], "engineer_user_id": stack.engineer_user_id,
            "db_rows_sites": stack.sql("SELECT id, name, slug FROM dcim_site ORDER BY id"),
            "db_rows_engineer": stack.sql("SELECT id, username, is_superuser FROM users_user ORDER BY id")}


def observe(gate, stack, site, body, description, to_version):
    watch = lib.HoldWatch()
    rec = lib.Recorder(stack.base)
    query = SQL_TO if to_version else SQL_FROM
    rows_before = stack.sql(query)
    status, parsed, text = rec.call(description, "POST", "/api/ipam/prefixes/", body=body,
                                    headers=stack.engineer)
    new_id = parsed.get("id") if status == 201 and isinstance(parsed, dict) else None
    rows_after = stack.sql(query)
    row = row_for(rows_after, new_id)
    if to_version:
        ct_rows = stack.sql(SQL_CT)
        ct = ct_rows[1].split("|")[0] if len(ct_rows) == 2 else None
        right = {"scope_type_id": ct, "scope_id": str(site), "_site_id": str(site), "status": "active"}
    else:
        ct_rows = None
        right = {"site_id": str(site), "status": "active"}
    stored = {k: row[k] for k in right} if row else None
    witness = None
    if new_id is not None:
        _, got, _ = rec.call("second witness: superuser reads the prefix", "GET",
                             "/api/ipam/prefixes/%d/" % new_id, headers=stack.admin, excerpt=300)
        if isinstance(got, dict):
            witness = {k: got.get(k) for k in ("id", "prefix", "status", "site", "scope_type", "scope_id", "scope")
                       if k in got}
            for key in ("site", "scope", "status"):
                if isinstance(witness.get(key), dict):
                    witness[key] = {k: witness[key].get(k) for k in ("id", "name", "value") if k in witness[key]}
    return {
        "gate": gate, "acting_user": "neteng (not a superuser; permissions %s)" % [p[0] for p in PERMISSIONS],
        "calls": rec.calls,
        "application_answer": {"status": status, "body_excerpt": text[:700]},
        "reported_success": status == 201, "success_criterion": "HTTP 201",
        "returned_id": new_id,
        "db_query": query, "db_rows_before": rows_before, "db_rows_after": rows_after,
        "db_rows_content_type_dcim_site": ct_rows,
        "stored_value": stored, "right_value": right, "stored_equals_right": stored == right,
        "second_witness_superuser_get": witness,
        "hold": watch.record(),
    }


def make_repeat(kind, pins):
    def run(repeat):
        lib.log("L3 %s repeat %d: bring-up" % (kind, repeat))
        ref = FROM_REF if kind == "from" else TO_REF
        stack = netbox.Stack(CASE + kind[0], PORTS[kind], pins, ref).bring_up()
        setup = set_up(stack)
        site = setup["site_id"]
        evidence = {"repeat": repeat, "image": ref, "pulled_ref": pins[ref]["pulled_ref"],
                    "instance_started_utc": stack.started_utc, "instance_ready_utc": stack.ready_utc,
                    "conditions": stack.conditions(), "setup": setup, "observations": []}
        if kind == "from":
            evidence["observations"].append(observe(
                "A", stack, site, old_workflow_body(site), "old workflow exactly as sealed, from-version", False))
        else:
            evidence["observations"].append(observe(
                "B", stack, site, old_workflow_body(site), "old workflow exactly as sealed, to-version", True))
            evidence["observations"].append(observe(
                "C", stack, site, correct_path_body(site),
                "correct path as sealed, to-version, on a second prefix at the same site", True))
        lib.log("L3 %s repeat %d: done" % (kind, repeat))
        return evidence
    return run


REUSED = []


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
                                                      "..", "..", "results", "L3.json"))
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
                 "stored_equals_right": o["stored_equals_right"]} for i, o in enumerate(obs)]

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
                           "permissions view/add/change on ipam.prefix and view on dcim.site, and its own API token",
            "settings_that_matter": "image defaults (ENFORCE_GLOBAL_UNIQUE at the release default); no plugins",
            "gate_B_and_C": "the same to-version instance serves B (192.0.2.0/24) and C (198.51.100.0/24), both at site HQ",
            "parallelism": "from-version and to-version stacks ran side by side on two ports; they share nothing",
        },
        "sealed": {
            "old_workflow_steps": sealed["old_workflow_steps"],
            "correct_path_on_to_version": sealed["correct_path_on_to_version"],
            "database_outcome": sealed["database_outcome"],
            "predicted_disposition": predicted, "prediction_detail": sealed["prediction_detail"],
        },
        "requests_as_run": {
            "old_workflow": "POST /api/ipam/prefixes/ with {\"prefix\": \"192.0.2.0/24\", \"site\": S, "
                            "\"status\": \"active\"}, header Authorization: Token <redacted>; HTTP 201 is success",
            "correct_path": "POST /api/ipam/prefixes/ with {\"prefix\": \"198.51.100.0/24\", \"scope_type\": "
                            "\"dcim.site\", \"scope_id\": S, \"status\": \"active\"}",
            "stored_value_read": "ipam_prefix row of the returned id, with psql inside the PostgreSQL container",
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
        "disposition_rule": "protocol README table, applied mechanically to the observations below",
        "prediction": {"sealed": predicted, "observed": disposition, "right": predicted == disposition},
        "deviations": [],
        "flags": [],
        "notes": ["Gate C uses a second prefix (198.51.100.0/24) at the same site on the instance that served "
                  "gate B, so the two prefixes are separate records; the request is otherwise the sealed correct path."],
        "repeats_taken_from_an_earlier_execution_of_this_script": sorted(REUSED),
        "repeats": {"from_version": from_repeats, "to_version": to_repeats},
        "times_utc": {"started": started, "finished": lib.utc_now(), "clock": "date -u on the host"},
        "free_disk_gib_at_end": lib.free_disk_gib(),
    }
    lib.write_json(args.out, result)
    print(disposition, summary)


if __name__ == "__main__":
    main()

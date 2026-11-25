#!/usr/bin/env python3
"""N6: ERPNext v15.126.0 -> v16.0.0, default list order changes from last-modified to creation.

One repeat against a freshly brought-up pair of sites. Set-up through the application's REST API as
Administrator, the sealed old workflow as the acting account (gate A on the old release, gate B on the new
one), the correct path (gate C on the new release, separate quotations) and the database reads. Writes raw
evidence only; `assemble.py` derives the disposition.

  SCREEN_OUT_DIR=<dir> SCREEN_HOLD_FILE=<marker> ./run_case.py <repeat number>
"""
import os
import sys
import time
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import screenlib as lib  # noqa: E402

ACTING_USER = "stage2_author@isolated.local"
COMPANY = "Stage2 Qual Corp"
ITEM = "STAGE2-UNIT"  # seeded non-stock item
CUSTOMER = "CUST-Q"
# Sealed step 1, verbatim; gate C adds the order.
LIST_PATH = '/api/resource/Quotation?filters=[["docstatus","=",0]]&limit_page_length=1'
LIST_PATH_CORRECT = LIST_PATH + "&order_by=modified desc"
PAUSE_SECONDS = 2  # between the two creations and the later edit, so the three timestamps differ clearly


def q(path):
    return urllib.parse.quote(path, safe="/?=&%")


def sql_rows(rec, events, label, state, database, sql):
    """Read rows straight from MariaDB in the database container (root password from the container's own env)."""
    shell = f'mariadb -uroot -p"$MARIADB_ROOT_PASSWORD" {database} --batch -e "$1"'
    done = rec.command(events, label, ["docker", "exec", state["mariadbContainer"], "sh", "-c", shell, "sh", sql],
                       shown=f"docker exec {state['mariadbContainer']} mariadb -uroot -p<redacted> {database} --batch -e \"{sql}\"")
    lines = [line for line in done.stdout.split("\n") if line != ""]
    if not lines:
        return []
    names = lines[0].split("\t")
    return [dict(zip(names, line.split("\t"))) for line in lines[1:]]


def admin_session(rec, events, base, password):
    r = rec.http(events, "set-up: Administrator log-in", "POST", base, "/api/method/login", {},
                 "none", {"usr": "Administrator", "pwd": password},
                 recorded_body={"usr": "Administrator", "pwd": "<redacted>"})
    sid = None
    for value in (r["headers"].get_all("Set-Cookie") or []):
        if value.startswith("sid="):
            sid = value.split(";")[0]
    return {"Cookie": sid or ""}


def common_setup(rec, events, release, state):
    """Per site, once: the acting account becomes a sales manager; one customer."""
    base, note = release["url"], "session of Administrator"
    admin = admin_session(rec, events, base, state["password"])
    user = rec.http(events, "set-up: read the acting account", "GET", base, q(f"/api/resource/User/{ACTING_USER}"),
                    admin, note)
    roles = [row["role"] for row in user["json"]["data"]["roles"]]
    for role in ("Sales User", "Sales Manager"):
        if role not in roles:
            roles.append(role)
    rec.http(events, "set-up: roles of the acting account (adds Sales User, Sales Manager)", "PUT", base,
             q(f"/api/resource/User/{ACTING_USER}"), admin, note, {"roles": [{"role": r} for r in roles]})
    rec.http(events, f"set-up: customer {CUSTOMER}", "POST", base, "/api/resource/Customer", admin, note,
             {"customer_name": CUSTOMER, "customer_type": "Company"}, timeout=300)
    return admin


def quotation_rows(rec, events, state, database, when):
    return sql_rows(rec, events, f"database read {when}: all quotations", state, database,
                    "SELECT name, docstatus, status, creation, modified, owner, modified_by FROM `tabQuotation` "
                    "ORDER BY creation")


def gate(rec, state, side, admin, label, correct_path):
    release, database = state[side], state[side]["database"]
    events = []
    gaps_before = rec.gaps()
    base, admin_note = release["url"], "session of Administrator"
    # Set-up: no draft may be left from an earlier gate on this site; then Q1, Q2, and a later edit of Q1.
    for row in quotation_rows(rec, events, state, database, "before set-up"):
        if row["docstatus"] == "0":
            rec.http(events, f"set-up: delete the earlier gate's remaining draft {row['name']}", "DELETE", base,
                     q(f"/api/resource/Quotation/{row['name']}"), admin, admin_note, timeout=300)
    names = []
    for n in (1, 2):
        made = rec.http(events, f"set-up: draft quotation Q{n} ({label})", "POST", base, "/api/resource/Quotation",
                        admin, admin_note,
                        {"quotation_to": "Customer", "party_name": CUSTOMER, "company": COMPANY,
                         "items": [{"item_code": ITEM, "qty": n, "rate": 100}]}, timeout=300)
        names.append(made["json"]["data"]["name"] if isinstance(made["json"], dict) and "data" in made["json"] else None)
        time.sleep(PAUSE_SECONDS)
    q1, q2 = names
    rec.http(events, "set-up: revise Q1 after Q2 exists", "PUT", base, q(f"/api/resource/Quotation/{q1}"),
             admin, admin_note, {"terms": "Revised: delivery within 30 days."}, timeout=300)
    before = quotation_rows(rec, events, state, database, "before the workflow")

    actor = {"Authorization": "token " + release["seed"]["authorToken"]}
    note = f"API key of {ACTING_USER}"
    list_path = LIST_PATH_CORRECT if correct_path else LIST_PATH
    listed = rec.http(events, "workflow step 1: list draft quotations, take the first", "GET", base, q(list_path),
                      actor, note, timeout=300)
    first = None
    if isinstance(listed["json"], dict) and listed["json"].get("data"):
        first = listed["json"]["data"][0].get("name")
    submit_path = f"/api/resource/Quotation/{first}"
    submitted = rec.http(events, "workflow step 2: submit that quotation", "PUT", base, q(submit_path), actor, note,
                         {"docstatus": 1}, timeout=300)
    after = quotation_rows(rec, events, state, database, "after the workflow")
    by_name = {row["name"]: row for row in after}
    stored = {"Q1": q1, "Q2": q2, "taken_by_the_workflow": first,
              "Q1_docstatus": by_name.get(q1, {}).get("docstatus"),
              "Q2_docstatus": by_name.get(q2, {}).get("docstatus")}
    statuses = [listed["status"], submitted["status"]]
    return {
        "release_tag": release["tag"], "database": database,
        "workflow_requests": [{"method": "GET", "path": list_path},
                              {"method": "PUT", "path": submit_path, "body": {"docstatus": 1}}],
        "workflow_response_status": statuses,
        "reported_success": statuses == [200, 200],
        "stored": stored, "right": {"Q1_docstatus": 1, "Q2_docstatus": 0},
        "stored_is_right": stored["Q1_docstatus"] == "1" and stored["Q2_docstatus"] == "0",
        "database_before": before, "database_after": after,
        "overlapped_hold": lib.overlapped_hold(events, gaps_before, rec.gaps()),
        "events": events,
    }


def main():
    repeat = int(sys.argv[1])
    out_dir = os.environ["SCREEN_OUT_DIR"]
    waited = lib.wait_for_no_hold()
    state = lib.load_state("erpnext.json")
    rec = lib.Recorder()
    result = {
        "case": "N6", "repeat": repeat, "started_utc": lib.utc_now(), "waited_for_hold_seconds": waited,
        "images": lib.image_pins([f"frappe/erpnext:{state['old']['tag']}", f"frappe/erpnext:{state['new']['tag']}",
                                  "mariadb:10.6", "redis:6.2-alpine"], platform=state.get("platform")),
        "setup": {"events": []},
    }
    setup = result["setup"]["events"]
    admins = {}
    for side in ("old", "new"):
        admins[side] = common_setup(rec, setup, state[side], state)
        sql_rows(rec, setup, f"{side}: settings that matter", state, state[side]["database"],
                 "SELECT doctype, field, value FROM `tabSingles` WHERE doctype = 'System Settings' "
                 "AND field IN ('time_zone', 'setup_complete', 'country') ORDER BY field")
        sql_rows(rec, setup, f"{side}: installed versions", state, state[side]["database"],
                 "SELECT app_name, app_version FROM `tabInstalled Application` ORDER BY idx")
        sql_rows(rec, setup, f"{side}: roles of the acting account", state, state[side]["database"],
                 f"SELECT role FROM `tabHas Role` WHERE parent = '{ACTING_USER}' ORDER BY role")
    lib.wait_for_no_hold()
    result["gate_A"] = gate(rec, state, "old", admins["old"], "gate A", correct_path=False)
    lib.wait_for_no_hold()
    result["gate_B"] = gate(rec, state, "new", admins["new"], "gate B", correct_path=False)
    lib.wait_for_no_hold()
    result["gate_C"] = gate(rec, state, "new", admins["new"], "gate C", correct_path=True)
    result["process_stopped_gaps"] = rec.gaps()
    result["finished_utc"] = lib.utc_now()
    lib.write_json(os.path.join(out_dir, f"repeat-{repeat}.json"), result)
    for g in ("gate_A", "gate_B", "gate_C"):
        r = result[g]
        print(g, r["release_tag"], "status", r["workflow_response_status"], "stored", r["stored"],
              "right" if r["stored_is_right"] else "NOT right", "hold-overlap" if r["overlapped_hold"] else "")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""N1: ERPNext v15.53.0 -> v15.54.0, Sales Invoice stops fetching the project's timesheets by itself.

One repeat against a freshly brought-up pair (../../../bringup/erpnext-up.sh v15.53.0 v15.54.0).
Set-up through the application's REST API as Administrator, the sealed old workflow as the acting account
(gate A on the old release, gate B on the new one), the correct path (gate C on the new release, separate
case data) and the database reads. Writes raw evidence only; `assemble.py` derives the disposition.

  SCREEN_OUT_DIR=<dir> SCREEN_HOLD_FILE=<marker> ./run_case.py <repeat number>
"""
import json
import os
import sys
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import screenlib as lib  # noqa: E402

ACTING_USER = "stage2_author@isolated.local"
COMPANY = "Stage2 Qual Corp"
ITEM = "SVC-A"
ACTIVITY = "Consulting-A"


def q(path):
    return urllib.parse.quote(path, safe="/?=&[]\",:%")


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


def post(rec, events, label, base, auth, note, path, body):
    return rec.http(events, label, "POST", base, q(path), auth, note, body, timeout=300)


def common_setup(rec, events, release, state):
    """Per site, once: the acting account's roles, the service item, the activity type."""
    base = release["url"]
    admin = admin_session(rec, events, base, state["password"])
    note = "session of Administrator"
    user = rec.http(events, "set-up: read the acting account", "GET", base, q(f"/api/resource/User/{ACTING_USER}"),
                    admin, note)
    roles = [row["role"] for row in user["json"]["data"]["roles"]]
    for role in ("Accounts User", "Projects User"):
        if role not in roles:
            roles.append(role)
    rec.http(events, "set-up: roles of the acting account (adds Projects User)", "PUT", base,
             q(f"/api/resource/User/{ACTING_USER}"), admin, note, {"roles": [{"role": r} for r in roles]})
    post(rec, events, "set-up: service item", base, admin, note, "/api/resource/Item",
         {"item_code": ITEM, "item_name": "Consulting hour", "item_group": "Services", "stock_uom": "Hour",
          "is_stock_item": 0})
    post(rec, events, "set-up: activity type", base, admin, note, "/api/resource/Activity Type",
         {"activity_type": ACTIVITY, "billing_rate": 100, "costing_rate": 0})
    return admin


def case_data(rec, events, release, admin, suffix):
    """Customer CUST-<suffix>, project PROJ-<suffix>, one submitted timesheet with one billable 8-hour row."""
    base, note = release["url"], "session of Administrator"
    customer, project = f"CUST-{suffix}", f"PROJ-{suffix}"
    post(rec, events, f"set-up: customer {customer}", base, admin, note, "/api/resource/Customer",
         {"customer_name": customer, "customer_type": "Company"})
    made = post(rec, events, f"set-up: project {project}", base, admin, note, "/api/resource/Project",
                {"project_name": project, "company": COMPANY, "customer": customer})
    made_name = made["json"]["data"]["name"]
    if made_name != project:
        # The project's document name comes from a naming series; rename it so the sealed request's
        # "project": "PROJ-A" addresses it literally.
        post(rec, events, f"set-up: rename project {made_name} to {project}", base, admin, note,
             "/api/method/frappe.client.rename_doc",
             {"doctype": "Project", "old_name": made_name, "new_name": project})
    sheet = post(rec, events, f"set-up: submitted timesheet on {project}", base, admin, note, "/api/resource/Timesheet",
                 {"company": COMPANY, "docstatus": 1,
                  "time_logs": [{"activity_type": ACTIVITY, "from_time": "2026-03-02 09:00:00", "hours": 8,
                                 "project": project, "is_billable": 1, "billing_hours": 8, "billing_rate": 100}]})
    return customer, project, sheet["json"]["data"]["name"]


def read_stored(rec, events, state, database, customer, timesheet, when):
    invoices = sql_rows(rec, events, f"database read {when}: Sales Invoice rows of {customer}", state, database,
                        "SELECT name, docstatus, status, customer, project, total_billing_hours, total_billing_amount, "
                        f"grand_total, owner FROM `tabSales Invoice` WHERE customer = '{customer}' ORDER BY creation")
    rows = sql_rows(rec, events, f"database read {when}: Sales Invoice Timesheet rows of {customer}", state, database,
                    "SELECT t.name, t.parent, t.time_sheet, t.timesheet_detail, t.billing_hours, t.billing_amount "
                    "FROM `tabSales Invoice Timesheet` t JOIN `tabSales Invoice` s ON s.name = t.parent "
                    f"WHERE s.customer = '{customer}' ORDER BY t.idx")
    sheets = sql_rows(rec, events, f"database read {when}: Timesheet {timesheet}", state, database,
                      "SELECT name, docstatus, status, per_billed, total_billable_hours, total_billed_hours "
                      f"FROM `tabTimesheet` WHERE name = '{timesheet}'")
    details = sql_rows(rec, events, f"database read {when}: Timesheet Detail rows of {timesheet}", state, database,
                       "SELECT name, parent, project, is_billable, billing_hours, sales_invoice "
                       f"FROM `tabTimesheet Detail` WHERE parent = '{timesheet}'")
    return {"sales_invoices": invoices, "sales_invoice_timesheets": rows, "timesheets": sheets,
            "timesheet_details": details}


def is_right(stored, timesheet):
    """The sealed right value: one Sales Invoice Timesheet row for the invoice with the timesheet and 8 billing
    hours; invoice submitted with total_billing_hours 8; timesheet 100 % billed with status Billed; the
    timesheet detail row points at the invoice."""
    def num(text):
        try:
            return float(text)
        except (TypeError, ValueError):
            return None

    if len(stored["sales_invoices"]) != 1:
        return False
    invoice = stored["sales_invoices"][0]
    rows, sheets, details = stored["sales_invoice_timesheets"], stored["timesheets"], stored["timesheet_details"]
    return (invoice["docstatus"] == "1" and num(invoice["total_billing_hours"]) == 8
            and len(rows) == 1 and rows[0]["parent"] == invoice["name"] and rows[0]["time_sheet"] == timesheet
            and num(rows[0]["billing_hours"]) == 8
            and len(sheets) == 1 and num(sheets[0]["per_billed"]) == 100 and sheets[0]["status"] == "Billed"
            and len(details) == 1 and details[0]["sales_invoice"] == invoice["name"])


def summarise(stored):
    invoice = stored["sales_invoices"][0] if stored["sales_invoices"] else {}
    sheet = stored["timesheets"][0] if stored["timesheets"] else {}
    detail = stored["timesheet_details"][0] if stored["timesheet_details"] else {}
    return {"sales_invoice_rows": len(stored["sales_invoices"]), "invoice": invoice.get("name"),
            "invoice_docstatus": invoice.get("docstatus"),
            "sales_invoice_timesheet_rows": len(stored["sales_invoice_timesheets"]),
            "total_billing_hours": invoice.get("total_billing_hours"),
            "timesheet_per_billed": sheet.get("per_billed"), "timesheet_status": sheet.get("status"),
            "timesheet_detail_sales_invoice": detail.get("sales_invoice")}


RIGHT = {"sales_invoice_timesheet_rows": 1, "billing_hours": 8, "total_billing_hours": 8, "invoice_docstatus": 1,
         "timesheet_per_billed": 100, "timesheet_status": "Billed", "timesheet_detail_sales_invoice": "the invoice"}


def gate(rec, state, side, admin, suffix, correct_path):
    release, database = state[side], state[side]["database"]
    events = []
    gaps_before = rec.gaps()
    base = release["url"]
    customer, project, timesheet = case_data(rec, events, release, admin, suffix)
    actor = {"Authorization": "token " + release["seed"]["authorToken"]}
    note = f"API key of {ACTING_USER}"
    before = read_stored(rec, events, state, database, customer, timesheet, "before the workflow")
    invoice = {"customer": customer, "company": COMPANY, "project": project,
               "items": [{"item_code": ITEM, "qty": 8, "rate": 100}]}
    requests = []
    if correct_path:
        # The page's Fetch Timesheet button: call the document method add_timesheet_data on the unsaved draft,
        # then create and submit the invoice with the rows it returned.
        draft = {"doctype": "Sales Invoice", "__islocal": 1, "__unsaved": 1, **invoice}
        fetched = post(rec, events, "correct path: add_timesheet_data on the draft", base, actor, note,
                       "/api/method/run_doc_method", {"docs": json.dumps(draft), "method": "add_timesheet_data"})
        requests.append({"method": "POST", "path": "/api/method/run_doc_method",
                         "body": {"docs": draft, "method": "add_timesheet_data"}})
        rows = []
        if isinstance(fetched["json"], dict) and fetched["json"].get("docs"):
            for row in fetched["json"]["docs"][0].get("timesheets", []):
                rows.append({k: row.get(k) for k in ("time_sheet", "timesheet_detail", "billing_hours",
                                                     "billing_amount", "activity_type", "description")})
        invoice["timesheets"] = rows
    body = {**invoice, "docstatus": 1}
    sent = post(rec, events, "workflow: create and submit the Sales Invoice in one call", base, actor, note,
                "/api/resource/Sales Invoice", body)
    requests.append({"method": "POST", "path": "/api/resource/Sales Invoice", "body": body})
    after = read_stored(rec, events, state, database, customer, timesheet, "after the workflow")
    return {
        "release_tag": release["tag"], "database": database,
        "case_data": {"customer": customer, "project": project, "timesheet": timesheet},
        "workflow_requests": requests, "workflow_response_status": sent["status"],
        "reported_success": sent["status"] == 200,
        "stored": summarise(after), "right": RIGHT, "stored_is_right": is_right(after, timesheet),
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
        "case": "N1", "repeat": repeat, "started_utc": lib.utc_now(), "waited_for_hold_seconds": waited,
        "images": lib.image_pins([f"frappe/erpnext:{state['old']['tag']}", f"frappe/erpnext:{state['new']['tag']}",
                                  "mariadb:10.6", "redis:6.2-alpine"], platform="linux/amd64"),
        "setup": {"events": []},
    }
    setup = result["setup"]["events"]
    admins = {}
    for side in ("old", "new"):
        admins[side] = common_setup(rec, setup, state[side], state)
        sql_rows(rec, setup, f"{side}: settings that matter", state, state[side]["database"],
                 "SELECT doctype, field, value FROM `tabSingles` WHERE (doctype = 'Projects Settings') OR "
                 "(doctype = 'System Settings' AND field IN ('time_zone', 'setup_complete', 'country')) "
                 "ORDER BY doctype, field")
        sql_rows(rec, setup, f"{side}: installed versions", state, state[side]["database"],
                 "SELECT app_name, app_version FROM `tabInstalled Application` ORDER BY idx")
        sql_rows(rec, setup, f"{side}: roles of the acting account", state, state[side]["database"],
                 f"SELECT role FROM `tabHas Role` WHERE parent = '{ACTING_USER}' ORDER BY role")
    lib.wait_for_no_hold()
    result["gate_A"] = gate(rec, state, "old", admins["old"], "A", correct_path=False)
    lib.wait_for_no_hold()
    result["gate_B"] = gate(rec, state, "new", admins["new"], "A", correct_path=False)
    lib.wait_for_no_hold()
    result["gate_C"] = gate(rec, state, "new", admins["new"], "C", correct_path=True)
    result["process_stopped_gaps"] = rec.gaps()
    result["finished_utc"] = lib.utc_now()
    lib.write_json(os.path.join(out_dir, f"repeat-{repeat}.json"), result)
    for g in ("gate_A", "gate_B", "gate_C"):
        r = result[g]
        print(g, r["release_tag"], "status", r["workflow_response_status"], "stored", r["stored"],
              "right" if r["stored_is_right"] else "NOT right", "hold-overlap" if r["overlapped_hold"] else "")


if __name__ == "__main__":
    main()

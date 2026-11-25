#!/usr/bin/env python3
"""N2: Dolibarr 18.0.9 -> 19.0.2, sales order delivery date through the REST API.

One command runs gates A, B and C, three repeats each, every repeat on an instance
started from nothing, and writes ../../results/N2.json:

    SCREEN_SCRATCH=/some/dir [SCREEN_HOLD_FILE=/path/HOLD] python3 run.py

The old workflow's request, the correct path and the right value are taken from the
sealed list (screen-list.json, case N2) and are not changed here.
"""
import argparse
import http.cookiejar
import os
import re
import sys
import time
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib  # noqa: E402

CASE = "N2"
PORT = 28610
BASE = "http://127.0.0.1:%d" % PORT
APP_REPO, DB_REPO = "dolibarr/dolibarr", "mariadb"
FROM_REF, TO_REF, DB_REF = "dolibarr/dolibarr:18.0.9", "dolibarr/dolibarr:19.0.2", "mariadb:10.6"

# Fixed by the sealed list.
ORDER_DATE = 1795478400
DELIVERY = 1797292800
RIGHT_VALUE = "2026-12-15 00:00:00"


def old_workflow_body(socid):
    return {"socid": socid, "date": ORDER_DATE, "date_livraison": DELIVERY}


def correct_path_body(socid):
    return {"socid": socid, "date": ORDER_DATE, "delivery_date": DELIVERY}


# Rights the administrator grants the sales user on the permissions page:
# 81 read sales orders, 82 create/modify sales orders, 121 read third parties,
# 342 modify its own user (Dolibarr requires it before a user may issue its own API key).
SALES_RIGHTS = [81, 82, 121, 342]


class AdminWeb:
    """The administrator's browser session, used only for the permissions page."""

    def __init__(self, rec):
        self.rec = rec
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))

    def _open(self, step, path, form=None):
        data = urllib.parse.urlencode(form).encode() if form is not None else None
        with self.opener.open(urllib.request.Request(BASE + path, data=data), timeout=90) as resp:
            status, html = resp.status, resp.read().decode("utf-8", "replace")
        title = re.search(r"<title>([^<]*)", html)
        self.rec.calls.append({
            "step": step, "utc": lib.utc_now(), "method": "POST" if form is not None else "GET",
            "path": path, "request_body": form, "status": status,
            "response_body_excerpt": "html page, title: %s" % (title.group(1).strip() if title else "?"),
            "response_body_length": len(html), "surface": "admin web session"})
        return status, html

    def login(self, user, password):
        _, html = self._open("admin opens the login page", "/index.php")
        token = lib.add_secret(re.search(r'name="token" value="([^"]+)"', html).group(1))
        _, html = self._open("admin logs in", "/index.php?mainmenu=home", {
            "token": token, "actionlogin": "login", "loginfunction": "loginfunction",
            "username": user, "password": password})
        if "logout" not in html.lower():
            raise RuntimeError("admin web login failed")

    def grant(self, user_id, right_ids):
        _, html = self._open("admin opens the user's permissions page", "/user/perms.php?id=%d" % user_id)
        for rid in right_ids:
            token = lib.add_secret(re.search(r'name="anti-csrf-newtoken" content="([^"]+)"', html).group(1))
            _, html = self._open(
                "admin grants right %d" % rid,
                "/user/perms.php?id=%d&action=addrights&entity=1&rights=%d&confirm=yes&token=%s"
                % (user_id, rid, token))


def bring_up(app_ref, pins):
    net, db, app = "iu1b-n2-net", "iu1b-n2-db", "iu1b-n2-app"
    secrets = {"db_root": lib.new_secret(), "db_pass": lib.new_secret(),
               "admin_pass": lib.new_secret(12), "sales_pass": "Pw-" + lib.new_secret(12)}
    lib.add_secret(secrets["sales_pass"])
    started = lib.utc_now()
    lib.network_create(CASE, net)
    lib.run_container(CASE, db, pins[DB_REF]["pulled_ref"], network=net, alias="db", env={
        "MARIADB_ROOT_PASSWORD": secrets["db_root"], "MARIADB_DATABASE": "dolidb",
        "MARIADB_USER": "doli", "MARIADB_PASSWORD": secrets["db_pass"], "TZ": "UTC"})
    lib.run_container(CASE, app, pins[app_ref]["pulled_ref"], network=net, publish=[(PORT, 80)], env={
        "DOLI_DB_HOST": "db", "DOLI_DB_NAME": "dolidb", "DOLI_DB_USER": "doli",
        "DOLI_DB_PASSWORD": secrets["db_pass"], "DOLI_URL_ROOT": BASE,
        "DOLI_ADMIN_LOGIN": "admin", "DOLI_ADMIN_PASSWORD": secrets["admin_pass"],
        "DOLI_INSTALL_AUTO": "1", "DOLI_ENABLE_MODULES": "Societe,Commande,Api",
        "DOLI_COMPANY_NAME": "ScreenCo", "DOLI_COMPANY_COUNTRYCODE": "US",
        "PHP_INI_DATE_TIMEZONE": "UTC"})
    # The image installs itself, then starts Apache. The login page answers only after that.
    lib.wait_http(BASE + "/index.php", ok=lambda s, t: s == 200 and 'name="token"' in t, timeout=1800)
    deadline = time.time() + 300
    while "Activating module Api" not in lib.docker("logs", app, check=False).stdout:
        if time.time() > deadline:
            raise RuntimeError("install did not finish")
        time.sleep(2)
    return {"db": db, "app": app, "secrets": secrets, "started_utc": started, "ready_utc": lib.utc_now()}


def sql(inst, query):
    """Read straight from MariaDB in the database container. Returns raw tab-separated lines."""
    out = lib.docker("exec", "-e", "MYSQL_PWD=" + inst["secrets"]["db_pass"], inst["db"],
                     "mariadb", "-udoli", "dolidb", "-B", "-e", query).stdout
    return out.rstrip("\n").split("\n") if out.strip() else []


def conditions(inst):
    php_tz = lib.docker("exec", inst["app"], "php", "-r",
                        "echo date_default_timezone_get(), ' ', PHP_VERSION;", check=False).stdout.strip()
    return {
        "install": "fresh install by the image's own first-start routine (DOLI_INSTALL_AUTO=1); no in-place upgrade",
        "modules_enabled_through": "image environment DOLI_ENABLE_MODULES=Societe,Commande,Api",
        "php_timezone_and_version": php_tz,
        "mariadb_time": sql(inst, "SELECT @@global.time_zone, @@system_time_zone, NOW(), UTC_TIMESTAMP(), VERSION()"),
        "dolibarr_version_const": sql(inst, "SELECT name, value FROM llx_const WHERE name IN "
                                            "('MAIN_VERSION_LAST_INSTALL','MAIN_VERSION_LAST_UPGRADE') ORDER BY name"),
        "modules_const": sql(inst, "SELECT name, value FROM llx_const WHERE name IN "
                                   "('MAIN_MODULE_SOCIETE','MAIN_MODULE_COMMANDE','MAIN_MODULE_API','MAIN_MODULE_USER') ORDER BY name"),
        "container_memory": [m for m in lib.memory_snapshot() if m.startswith("iu1b-")],
    }


def set_up(inst, customers):
    """Administration through the application's own API and admin pages."""
    rec = lib.Recorder(BASE)
    sec = inst["secrets"]
    status, body, _ = rec.call("admin obtains an API key", "POST", "/api/index.php/login",
                               body={"login": "admin", "password": sec["admin_pass"], "reset": 1})
    admin_key = lib.add_secret(body["success"]["token"])
    hdr = {"DOLAPIKEY": admin_key}
    status, body, _ = rec.call("version check", "GET", "/api/index.php/status", headers=hdr)
    version = body["success"]["dolibarr_version"]
    socids = {}
    for name in customers:
        status, body, text = rec.call("admin creates customer %s" % name, "POST", "/api/index.php/thirdparties",
                                      body={"name": name, "client": 1, "code_client": "auto"}, headers=hdr)
        if status != 200:
            raise RuntimeError("customer set-up failed: %s %s" % (status, text[:200]))
        socids[name] = int(body)
    status, body, text = rec.call("admin creates the sales user", "POST", "/api/index.php/users",
                                  body={"login": "sales1", "lastname": "Sales", "firstname": "Sam",
                                        "pass": sec["sales_pass"], "employee": 1}, headers=hdr)
    if status != 200:
        raise RuntimeError("user set-up failed: %s %s" % (status, text[:200]))
    sales_id = int(body)
    web = AdminWeb(rec)
    web.login("admin", sec["admin_pass"])
    web.grant(sales_id, SALES_RIGHTS)
    status, body, text = rec.call("sales user obtains its own API key", "POST", "/api/index.php/login",
                                  body={"login": "sales1", "password": sec["sales_pass"], "reset": 1})
    if status != 200:
        raise RuntimeError("sales API key set-up failed: %s %s" % (status, text[:300]))
    sales_key = lib.add_secret(body["success"]["token"])
    rights = sql(inst, "SELECT fk_user, fk_id FROM llx_user_rights WHERE fk_user = %d ORDER BY fk_id" % sales_id)
    users = sql(inst, "SELECT rowid, login, admin, statut FROM llx_user ORDER BY rowid")
    return {"admin_key": admin_key, "sales_key": sales_key, "sales_user_id": sales_id, "socids": socids,
            "reported_version": version, "calls": rec.calls,
            "db_rows_sales_user_rights": rights, "db_rows_users": users}


ORDER_SQL = ("SELECT rowid, ref, fk_soc, fk_user_author, date_commande, date_livraison, fk_statut "
             "FROM llx_commande ORDER BY rowid")


def observe(gate, inst, setup, body, description):
    """One gate observation: the write as the sales user, then the stored row from MariaDB."""
    watch = lib.HoldWatch()
    rec = lib.Recorder(BASE)
    rows_before = sql(inst, ORDER_SQL)
    status, parsed, text = rec.call(description, "POST", "/api/index.php/orders", body=body,
                                    headers={"DOLAPIKEY": setup["sales_key"]})
    order_id = parsed if isinstance(parsed, int) and not isinstance(parsed, bool) else None
    reported_success = status == 200 and order_id is not None
    rows_after = sql(inst, ORDER_SQL)
    stored = None
    row_for_order = None
    if order_id is not None:
        row = sql(inst, "SELECT rowid, fk_soc, date_livraison, date_livraison IS NULL AS delivery_is_null "
                        "FROM llx_commande WHERE rowid = %d" % order_id)
        row_for_order = row
        if len(row) == 2:
            stored = row[1].split("\t")[2]
        # Second witness: the administrator reads the order back with a different credential.
        _, witness, _ = rec.call("second witness: admin reads the order", "GET",
                                 "/api/index.php/orders/%d" % order_id,
                                 headers={"DOLAPIKEY": setup["admin_key"]}, excerpt=300)
        witness = {k: witness.get(k) for k in ("id", "ref", "socid", "date", "date_commande",
                                               "date_livraison", "delivery_date", "statut")} \
            if isinstance(witness, dict) else None
    else:
        witness = None
    return {
        "gate": gate, "acting_user": "sales1 (non-admin; rights %s)" % SALES_RIGHTS,
        "calls": rec.calls,
        "application_answer": {"status": status, "body_excerpt": text[:600]},
        "reported_success": reported_success,
        "success_criterion": "HTTP 200 and the returned order id",
        "returned_order_id": order_id,
        "db_query": ORDER_SQL, "db_rows_before": rows_before, "db_rows_after": rows_after,
        "db_row_for_returned_id": row_for_order,
        "stored_value": stored, "right_value": RIGHT_VALUE,
        "stored_equals_right": stored == RIGHT_VALUE,
        "second_witness_admin_get": witness,
        "hold": watch.record(),
    }


def make_repeat(kind, pins):
    def run(repeat):
        app_ref = FROM_REF if kind == "from" else TO_REF
        lib.log("N2 %s repeat %d: bring-up %s" % (kind, repeat, app_ref))
        inst = bring_up(app_ref, pins)
        setup = set_up(inst, ["Customer X", "Customer Y"])
        evidence = {
            "repeat": repeat, "image": app_ref, "pulled_ref": pins[app_ref]["pulled_ref"],
            "instance_started_utc": inst["started_utc"], "instance_ready_utc": inst["ready_utc"],
            "reported_version": setup["reported_version"],
            "conditions": conditions(inst),
            "setup": {"calls": setup["calls"], "socids": setup["socids"],
                      "sales_user_id": setup["sales_user_id"],
                      "db_rows_sales_user_rights": setup["db_rows_sales_user_rights"],
                      "db_rows_users": setup["db_rows_users"]},
            "observations": [],
        }
        x, y = setup["socids"]["Customer X"], setup["socids"]["Customer Y"]
        if kind == "from":
            evidence["observations"].append(observe(
                "A", inst, setup, old_workflow_body(x), "old workflow exactly as sealed, from-version"))
        else:
            evidence["observations"].append(observe(
                "B", inst, setup, old_workflow_body(x), "old workflow exactly as sealed, to-version"))
            evidence["observations"].append(observe(
                "C", inst, setup, correct_path_body(y), "correct path as sealed, to-version, second customer"))
        return evidence
    return run


def classify(a, b, c):
    """Mechanical disposition by the table in the protocol README."""
    def n(obs, pred):
        return sum(1 for o in obs if pred(o))
    a_ok = n(a, lambda o: o["reported_success"] and o["stored_equals_right"])
    c_ok = n(c, lambda o: o["stored_equals_right"])
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
    parser.add_argument("--out", default=os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                      "..", "..", "results", "N2.json"))
    args = parser.parse_args()
    sealed = lib.sealed_case(CASE)
    scratch = lib.scratch_dir(CASE)
    started = lib.utc_now()
    lib.wait_hold()
    lib.teardown(CASE)

    pins, images = lib.pin_images(sealed, ((FROM_REF, APP_REPO), (TO_REF, APP_REPO), (DB_REF, DB_REPO)))

    from_repeats, to_repeats = [], []
    for i in range(1, args.repeats + 1):
        from_repeats.append(lib.run_repeat(CASE, make_repeat("from", pins), i))
        lib.write_json(os.path.join(scratch, "from-%d.json" % i), from_repeats[-1])
    for i in range(1, args.repeats + 1):
        to_repeats.append(lib.run_repeat(CASE, make_repeat("to", pins), i))
        lib.write_json(os.path.join(scratch, "to-%d.json" % i), to_repeats[-1])

    def pick(repeats, gate):
        return [o for r in repeats for o in r["observations"] if o["gate"] == gate]

    a, b, c = pick(from_repeats, "A"), pick(to_repeats, "B"), pick(to_repeats, "C")
    disposition, summary = classify(a, b, c)
    predicted = sealed["predicted_disposition"]
    result = {
        "schema": "gammatron-real-upgrade-screen-result/v1",
        "case_id": CASE, "screen_lane": "iu1-b",
        "app": sealed["app"], "from_version": sealed["from_version"], "to_version": sealed["to_version"],
        "images": images,
        "conditions": {
            "host": "macOS on Apple Silicon, Docker Desktop, linux/arm64 containers, all ports bound to 127.0.0.1",
            "install": "every repeat is a fresh install on an empty MariaDB; no in-place upgrade was run",
            "time_zone": "PHP date.timezone UTC (image default, set explicitly); MariaDB container TZ=UTC",
            "acting_role": "non-admin internal user sales1 with rights 81, 82, 121 and 342 granted by the "
                           "administrator on the permissions page; API key issued to the user by POST /login",
            "settings_that_matter": "modules Societe, Commande and Api enabled through the image's "
                                    "DOLI_ENABLE_MODULES; company country US; no other configuration",
            "gate_B_and_C": "the same to-version instance serves B (Customer X) and C (Customer Y) in each repeat",
            "per_repeat": "see conditions inside each repeat",
        },
        "sealed": {
            "old_workflow_steps": sealed["old_workflow_steps"],
            "correct_path_on_to_version": sealed["correct_path_on_to_version"],
            "database_outcome": sealed["database_outcome"],
            "predicted_disposition": predicted, "prediction_detail": sealed["prediction_detail"],
        },
        "requests_as_run": {
            "old_workflow": "POST /api/index.php/orders, header DOLAPIKEY: <redacted>, body "
                            "{\"socid\": X, \"date\": 1795478400, \"date_livraison\": 1797292800}",
            "correct_path": "POST /api/index.php/orders, header DOLAPIKEY: <redacted>, body "
                            "{\"socid\": Y, \"date\": 1795478400, \"delivery_date\": 1797292800}",
            "stored_value_read": "llx_commande.date_livraison for the returned order id, read with the "
                                 "mariadb client inside the database container",
        },
        "gates": {
            "A": {"what": "old workflow on the from-version", "pass": summary["gate_A_pass"]},
            "B": {"what": "identical steps on the to-version", "per_repeat": summary["gate_B_per_repeat"],
                  "observations_in_short": [
                      {"repeat": i + 1, "status": o["application_answer"]["status"],
                       "body": o["application_answer"]["body_excerpt"][:120],
                       "stored_value": o["stored_value"], "right_value": o["right_value"]}
                      for i, o in enumerate(b)]},
            "C": {"what": "correct path on the to-version", "pass": summary["gate_C_pass"]},
        },
        "disposition": disposition,
        "disposition_rule": "protocol README table, applied mechanically to the observations below",
        "prediction": {"sealed": predicted, "observed": disposition, "right": predicted == disposition},
        "deviations": [],
        "flags": [],
        "repeats": {"from_version": from_repeats, "to_version": to_repeats},
        "times_utc": {"started": started, "finished": lib.utc_now(), "clock": "date -u on the host"},
        "free_disk_gib_at_end": lib.free_disk_gib(),
    }
    lib.write_json(args.out, result)
    lib.teardown(CASE)
    print(disposition, summary)


if __name__ == "__main__":
    main()

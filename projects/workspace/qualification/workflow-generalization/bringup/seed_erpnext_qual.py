"""Idempotent seeder for the isolated ERPNext qualification sites (clocksmith/deco#88).

Creates three companies, one supplier, one item and two local users with API keys.
The user password comes from STAGE2_USER_PASSWORD; nothing secret is stored here.
Run inside the application container from sites/: ../env/bin/python /tmp/seed_erpnext_qual.py <site>
"""
import json
import os
import frappe
from frappe.core.doctype.user.user import generate_keys
from frappe.desk.page.setup_wizard.setup_wizard import setup_complete

def run_seed(site_name):
    frappe.init(site=site_name)
    frappe.connect()
    frappe.set_user("Administrator")

    if not frappe.db.get_single_value("System Settings", "setup_complete"):
        setup_complete({
            "currency": "USD",
            "full_name": "Stage2 Admin",
            "company_name": "Stage2 Qual Corp",
            "timezone": "UTC",
            "company_abbr": "S2Q",
            "industry": "Technology",
            "country": "United States",
            "fy_start_date": "2026-01-01",
            "fy_end_date": "2026-12-31",
            "language": "english",
        })
        frappe.db.commit()

    for cname, abbr in [("Stage2 Partner Corp", "S2P"), ("Stage2 Quarantine Corp", "S2X")]:
        if not frappe.db.exists("Company", cname):
            c = frappe.get_doc({
                "doctype": "Company",
                "company_name": cname,
                "abbr": abbr,
                "default_currency": "USD",
                "country": "United States",
            })
            c.insert(ignore_permissions=True)
            frappe.db.commit()

    if not frappe.db.exists("Supplier Group", "All Supplier Groups"):
        sg = frappe.get_doc({"doctype": "Supplier Group", "supplier_group_name": "All Supplier Groups", "is_group": 1})
        sg.insert(ignore_permissions=True)
        frappe.db.commit()

    if not frappe.db.exists("Supplier", "Stage2 Approved Vendor"):
        s = frappe.get_doc({
            "doctype": "Supplier",
            "supplier_name": "Stage2 Approved Vendor",
            "supplier_group": frappe.db.get_value("Supplier Group", {}, "name") or "All Supplier Groups",
            "supplier_type": "Company",
        })
        s.insert(ignore_permissions=True)
        frappe.db.commit()

    if not frappe.db.exists("Item", "STAGE2-UNIT"):
        ig = frappe.db.get_value("Item Group", {"is_group": 0}, "name") or frappe.db.get_value("Item Group", {}, "name")
        it = frappe.get_doc({
            "doctype": "Item",
            "item_code": "STAGE2-UNIT",
            "item_name": "Stage2 Qualified Service Unit",
            "item_group": ig,
            "stock_uom": "Nos",
            "is_stock_item": 0,
            "is_purchase_item": 1,
            "standard_rate": 100,
        })
        it.insert(ignore_permissions=True)
        frappe.db.commit()

    tokens = {}
    for email, first_name, roles in [
        ("stage2_author@isolated.local", "Stage2Author", ["Purchase User", "Purchase Manager", "Accounts User"]),
        ("stage2_approver@isolated.local", "Stage2Approver", ["Purchase Manager", "Purchase Master Manager", "System Manager"]),
    ]:
        if not frappe.db.exists("User", email):
            u = frappe.get_doc({
                "doctype": "User",
                "email": email,
                "first_name": first_name,
                "enabled": 1,
                "send_welcome_email": 0,
                "user_type": "System User",
                "new_password": os.environ["STAGE2_USER_PASSWORD"],
            })
            u.insert(ignore_permissions=True)
            for r in roles:
                if frappe.db.exists("Role", r):
                    u.append("roles", {"role": r})
            u.save(ignore_permissions=True)
        res = generate_keys(email)
        api_key = frappe.db.get_value("User", email, "api_key")
        tokens[email] = f"{api_key}:{res['api_secret']}"
        frappe.db.commit()

    # Ensure track_changes=1 on Supplier Quotation as well as Purchase Order for Version audit trail:
    frappe.db.set_value("DocType", "Purchase Order", "track_changes", 1)
    frappe.db.set_value("DocType", "Supplier Quotation", "track_changes", 1)
    frappe.clear_cache()
    frappe.db.commit()

    print("ERP_SEED_JSON:" + json.dumps({
        "site": site_name,
        "authorToken": tokens["stage2_author@isolated.local"],
        "approverToken": tokens["stage2_approver@isolated.local"],
        "companies": ["Stage2 Qual Corp", "Stage2 Partner Corp", "Stage2 Quarantine Corp"],
        "supplier": "Stage2 Approved Vendor",
        "item": "STAGE2-UNIT",
    }))

if __name__ == "__main__":
    import sys
    run_seed(sys.argv[1])

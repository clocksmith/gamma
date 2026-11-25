# Real-upgrade screen list: predictions before any run

Written 2026-11-25T13:12:19Z. **Nothing was run.** No container was started, no image pulled, no model called.
Every disposition below is a prediction from release notes, changelogs and upstream source read on
public hosts. Tag existence and compressed sizes are from Docker Hub.

Machine-readable copy: `screen-list.json` (same content).

## The rule being screened for

> A case qualifies if the old workflow worked before, still reports success after, and now persists the wrong result; verified against an independently specified database outcome; with the correct path shown to still work. Same role, task and intended business outcome before and after. Setup blocks, explicit rejections and self-healing are separate dispositions.

Dispositions: `silent-wrong-write`, `loud-failure` (error or explicit rejection), `setup-block` (the case
cannot be set up), `self-healing` (the application accepts the old steps and stores the right thing).

Proposed gates per candidate, three repeats each:

- A. Old workflow on the from-version: reports success and the database holds the right value, 3 of 3.
- B. Same steps on the to-version: reports success and the database holds a value other than the right one, 3 of 3. Any error or rejection is loud-failure; the right value is self-healing.
- C. Correct path on the to-version, same role: the database holds the right value, 3 of 3.
- A case that cannot be built on either release is setup-block, with the exact request and response recorded.

## Summary

- **12 candidates**, fixed here: the lane's five catalogued upgrades and seven new ones.
- Predicted dispositions: 11 `silent-wrong-write`, 1 `setup-block`, 0 `loud-failure`, 0 `self-healing`.
- One of the eleven silent predictions (L5) cannot qualify: the upgraded release has no correct path for the old outcome.
- A predicted disposition is the single most likely outcome. Summing the rough chances, about 6 or 7 of the 11 runnable
  candidates are expected to qualify if all are run; base rates say some of these readings will be wrong.
- **All five catalogued mocks differ from the real software on the decisive behaviour.** Each mock answers 4xx to the
  old request; by source reading the real release does not reject it in any of the five (L4 on a licensed
  instance). For three of them (L1, L2, L3) that makes the real case a predicted silent wrong write, not the
  loud failure the mock models.
- Run first: **N1** (ERPNext v15.53.0 to v15.54.0), **N3** (OpenProject 13.4.0 to 14.0.0), **N2** (Dolibarr 18.0.9 to 19.0.2).

Two cautions:

- The earlier screens held one workflow fixed and varied the release, and found nothing. This list starts from documented changes and picks the workflow each one touches. A hit here therefore says nothing about how often an arbitrary workflow meets a silent wrong write, just as 'none found' in 38 pairs said nothing about rarity.
- Six of the eleven predicted silent cases (L1, L2, L3, N2, N3, N5) are one mechanism: the server accepts a request that carries a property it no longer acts on. Four (N1, N4, N6, L5) are a changed default, and one (N7) a changed reading of the same text. In the first group the new release never errors, and a read of the record after the write shows the miss. For a workflow driven through the page those six upgrades mostly remove or relabel the control, which is loud; N1, N4 and N6 are the ones predicted silent through the page as well.

## The list, ranked by how likely each is a real silent wrong write

| Rank | Id | Application | From | To | Predicted | Confidence | Chance it qualifies (rough) | Run first |
| ---: | --- | --- | --- | --- | --- | --- | ---: | --- |
| 1 | N1 | ERPNext | v15.53.0 | v15.54.0 | `silent-wrong-write` | high | 0.80 | yes |
| 2 | N2 | Dolibarr ERP/CRM | 18.0.9 | 19.0.2 | `silent-wrong-write` | high | 0.80 | yes |
| 3 | L3 | NetBox | v4.1.11 | v4.2.0 | `silent-wrong-write` | high | 0.80 |  |
| 4 | L2 | NetBox | v4.0.11 | v4.1.0 | `silent-wrong-write` | high | 0.80 |  |
| 5 | N3 | OpenProject | 13.4.0 | 14.0.0 | `silent-wrong-write` | high | 0.75 | yes |
| 6 | L1 | OpenProject | 17.7.0 | 17.8.0 | `silent-wrong-write` | medium | 0.65 |  |
| 7 | N5 | Vikunja | 0.23.0 | 0.24.0 | `silent-wrong-write` | medium | 0.60 |  |
| 8 | N4 | OpenProject | 15.3.0 | 15.4.0 | `silent-wrong-write` | medium | 0.60 |  |
| 9 | N6 | ERPNext | v15.126.0 | v16.0.0 | `silent-wrong-write` | medium | 0.40 |  |
| 10 | N7 | NocoDB | 0.107.5 | 0.108.0 | `silent-wrong-write` | low | 0.30 |  |
| 11 | L5 | GitLab | 15.11.13 | 16.0.0 | `silent-wrong-write` | medium | 0.05 |  |
| 12 | L4 | GitLab | 15.11.13 | 16.0.0 | `setup-block` | high | 0.00 |  |

Ids starting with L are the lane's catalogued five; N are new. The chance column is the author's judgement.

### Why these three first

- **N1** (ERPNext v15.53.0 to v15.54.0): Highest confidence, upstream names the behaviour change, existing ERPNext bring-up, silent on both surfaces the lane uses.
- **N3** (OpenProject 13.4.0 to 14.0.0): Runs on the default tags of the existing OpenProject bring-up (88 seconds measured); one request decides it.
- **N2** (Dolibarr ERP/CRM 18.0.9 to 19.0.2): Cheapest clean case on a new application; exact source lines at the exact image tags; small images.

Together: about 2749 MB of compressed downloads and about 8.0 GB on disk unpacked.
Bring-up: about 8 minutes in total (ERPNext 3, OpenProject 1.5, Dolibarr 3; the Dolibarr figure is an estimate). All gates: about 30 to 45 minutes for three candidates at three repeats per gate; the requests themselves take seconds.
Before any run: set-up additions for all three and a new bring-up script for Dolibarr, each frozen and hashed first. Unpacked sizes are estimated at 2.5 to 3 times the compressed size the registry reports. The lane's own preflight asks for 25 GiB free before pulling.

**Prediction for the first three:** At least one of the three qualifies under gates A, B and C. Author's estimate: about 0.95, allowing for a shared error in how the sources were read; expected number about 2.3 of 3.

L3 and L2 (NetBox) rank above N3 on likelihood. They are not in the first three because NetBox is a
network inventory rather than a business application, has no bring-up in the lane and starts slowly.
They are the natural fourth and fifth runs, since they test two of the lane's own mocks on the real thing.

## The lane's five catalogued upgrades against the real software

| Id | Catalogue entry | Real pair | Mock says | Real software, by source | Match |
| --- | --- | --- | --- | --- | --- |
| L1 | `openproject-17.8-target-versions` | 17.7.0 to 17.8.0 | After conversion the mock answers HTTP 422 'Schema mismatch for version/targetVersions' to a PATCH carrying _links.version. | No 422. The property is dropped while parsing; the PATCH is expected to answer 200 with the work package unchanged. | **no** |
| L2 | `netbox-4.0-to-4.1-vlangroup-vid-ranges` | v4.0.11 to v4.1.0 | On v4.1 the mock answers HTTP 400 {"min_vid": ["Removed in NetBox v4.1; use vid_ranges."]}. | No 400. min_vid and max_vid are not serializer fields any more, so they are ignored; the request succeeds and vid_ranges keeps its default. | **no** |
| L3 | `netbox-4.1-to-4.2-prefix-generic-scope` | v4.1.11 to v4.2.0 | On v4.2 the mock answers HTTP 400 {"site": ["Field site was removed in NetBox v4.2; use scope_type and scope_id."]}. | No 400. site is ignored, the other fields are applied, and the prefix is stored with no scope. | **no** |
| L4 | `gitlab-15.11-to-16.0-approval-rules` | 15.11.13 to 16.0.0 | On 16.0 the mock answers HTTP 400 'approvals_before_merge was removed in GitLab 16.0; use approval_rules API'. | Not removed in 16.0.0. On a licensed instance the same call is still accepted. | **no** |
| L5 | `gitlab-15.11-to-16.0-token-expires-at` | 15.11.13 to 16.0.0 | On 16.0 the mock answers HTTP 400 'expires_at is required in GitLab 16.0 (non-expiring tokens removed)' when expires_at is null. | No 400. expires_at stays optional; a null or missing value is silently replaced by a date 365 days ahead and the token is created. | **no** |

Details and upstream text for each are in the candidate sections.

## Candidates

### N1. ERPNext: v15.53.0 to v15.54.0

- **Rank** 1 of 12. Documented by upstream as a change of default behaviour for API users; silent on the API and on the page; runs on the lane's ERPNext bring-up.
- **Images:** `frappe/erpnext:v15.53.0` (amd64 520 MB); `frappe/erpnext:v15.54.0` (amd64 520 MB); `mariadb:10.6` (amd64 104 MB, arm64 98 MB); `redis:6.2-alpine` (amd64 12 MB, arm64 12 MB)
- **Surface:** REST API and the Desk page (both predicted silent)
- **Role:** Accounts user who may create and submit Sales Invoices and read Projects and Timesheets
- **Task:** Invoice customer CUST-A for the unbilled time on project PROJ-A
- **Intended business outcome:** A submitted Sales Invoice that carries the project's unbilled timesheet (8 billable hours) and marks that timesheet as billed, so the hours cannot be invoiced twice
- **Old workflow, as it works on the from-version:**
  1. POST /api/resource/Sales Invoice with {"customer": "CUST-A", "company": ..., "project": "PROJ-A", "items": [{"item_code": ..., "qty": 8, "rate": 100}], "docstatus": 1} (create and submit in one call)
  1. Treat HTTP 200 as success
- **Same task through the page:** New Sales Invoice; choose the customer; choose the project (on v15.53.0 the Time Sheets table then fills by itself); add the item row; Save; Submit. Predicted silent on v15.54.0 as well: the table stays empty and Save and Submit succeed.
- **Upstream change:** Up to v15.53.0 a Sales Invoice with a project and no timesheet rows fetched the project's unbilled timesheets on its own. From v15.54.0 that happens only if the new Projects Settings checkbox 'Fetch Timesheet in Sales Invoice' is on; its default is off and no patch turns it on for existing sites.
  - Upstream text: "If you create Sales Invoices via API, you sometimes want to fetch unbilled timesheets from the linked project. So far, this was the default behavior. Now you'll need to make an additional API call" <https://github.com/frappe/erpnext/wiki/Migration-Guide-To-ERPNext-Version-16>
  - Source: v15.53.0: if not self.timesheets and self.project: self.add_timesheet_data() <https://github.com/frappe/erpnext/blob/v15.53.0/erpnext/accounts/doctype/sales_invoice/sales_invoice.py>
  - Source: v15.54.0: the same branch also requires self.is_auto_fetch_timesheet_enabled() <https://github.com/frappe/erpnext/blob/v15.54.0/erpnext/accounts/doctype/sales_invoice/sales_invoice.py>
  - Source: v15.54.0 Projects Settings: fetch_timesheet_in_sales_invoice, Check, default '0' <https://github.com/frappe/erpnext/blob/v15.54.0/erpnext/projects/doctype/projects_settings/projects_settings.json>
  - Source: v15.54.0 form script: the project trigger asks is_auto_fetch_timesheet_enabled before fetching <https://github.com/frappe/erpnext/blob/v15.54.0/erpnext/accounts/doctype/sales_invoice/sales_invoice.js>
  - Source: pull request and its version-15 backport <https://github.com/frappe/erpnext/pull/45908>
  - Source: backport <https://github.com/frappe/erpnext/pull/46142>
- **Prediction on the to-version:** `silent-wrong-write`. Every step answers 200 and the invoice is submitted. It carries no timesheet row, its billing hours are 0, and the timesheet stays unbilled.
  - Condition: None known; the setting defaults to off on a fresh site and after an in-place upgrade (no patch in patches.txt between the two tags touches it).
  - If the prediction is wrong, most likely: setup-block (billing fixtures or permissions not accepted as written)
- **Database outcome** (read via MariaDB in the database container, as the lane's ERPNext write step already does):
  - On the from-version: one row in `tabSales Invoice Timesheet` with parent = the invoice, time_sheet = the timesheet, billing_hours = 8; `tabSales Invoice`.total_billing_hours = 8; after submit `tabTimesheet`.per_billed = 100 and status = 'Billed'; `tabTimesheet Detail`.sales_invoice = the invoice
  - Right on the to-version: the same as on the from-version
  - Predicted stored on the to-version: no row in `tabSales Invoice Timesheet` for the invoice; total_billing_hours = 0; `tabTimesheet`.per_billed = 0 and status = 'Submitted'; `tabTimesheet Detail`.sales_invoice NULL
- **Correct path on the to-version:** Call the document method add_timesheet_data on the draft invoice before saving (the page's Fetch Timesheet button does this), or pass the timesheets rows explicitly; then submit.
- **Confidence:** high; rough chance it qualifies 0.80. Controller, form script and settings source at both exact tags, and upstream's own migration guide names it as a behaviour change for API users. Not run.
- **To run:** projects/workspace/qualification/workflow-generalization/bringup/erpnext-up.sh v15.53.0 v15.54.0. Set-up additions: customer, service item, project, activity type, one submitted timesheet with one billable 8-hour row on the project; roles for the acting account (Accounts User and Projects User). To be written and frozen before the run. About 1156 MB compressed, about 3.5 GB unpacked. Bring-up: about 3 minutes (3 min 9 s measured for the script's default pair); images are amd64 only, as were the pairs the lane already ran. Licence or account: none.
- **Overlap with earlier screens:** Neither tag was screened. The earlier ERPNext stride points v15.50.0 and v15.60.0 lie on either side of this change, but those screens used a Purchase Order terms write and supplier-quotation reads, which this change does not touch.

### N2. Dolibarr ERP/CRM: 18.0.9 to 19.0.2

- **Rank** 2 of 12. One removed fallback line between the two exact image tags; the REST handler accepts any key.
- **Images:** `dolibarr/dolibarr:18.0.9` (amd64 350 MB, arm64 343 MB); `dolibarr/dolibarr:19.0.2` (amd64 283 MB, arm64 273 MB); `mariadb:10.6` (amd64 104 MB, arm64 98 MB)
- **Surface:** REST API
- **Role:** Sales user with the right to create customer orders and an API key
- **Task:** Create a sales order for customer X with planned delivery on 2026-12-15
- **Intended business outcome:** The order exists and its planned delivery date is 2026-12-15
- **Old workflow, as it works on the from-version:**
  1. POST /api/index.php/orders with header DOLAPIKEY and body {"socid": X, "date": 1795478400, "date_livraison": 1797292800}
  1. Treat HTTP 200 and the returned order id as success
- **Upstream change:** 19.0 removes the deprecated order property date_livraison. Up to 18.0.x Commande::create() fell back to it when delivery_date was empty; from 19.0 only delivery_date is read. The REST handler copies every posted key onto the object without checking that it exists.
  - Upstream text: "The duplicated and deprecated property ->date_livraison that was renamed into ->delivery_date has been completely removed." <https://github.com/Dolibarr/dolibarr/blob/develop/ChangeLog>
  - Source: 18.0.9: $delivery_date = empty($this->delivery_date) ? $this->date_livraison : $this->delivery_date; <https://github.com/Dolibarr/dolibarr/blob/18.0.9/htdocs/commande/class/commande.class.php#L925>
  - Source: 19.0.2: $delivery_date = $this->delivery_date; <https://github.com/Dolibarr/dolibarr/blob/19.0.2/htdocs/commande/class/commande.class.php#L901>
  - Source: REST post(): foreach ($request_data as $field => $value) { $this->commande->$field = $value; } <https://github.com/Dolibarr/dolibarr/blob/19.0.2/htdocs/commande/class/api_orders.class.php>
- **Prediction on the to-version:** `silent-wrong-write`. The POST answers 200 with a new order id. The order is stored without a delivery date.
  - Condition: None known; same on a fresh install and after an in-place upgrade.
  - If the prediction is wrong, most likely: setup-block (API key or module activation through the image's environment not working as assumed)
- **Database outcome** (read via MariaDB in the database container; GET /api/index.php/orders/{id} as a second witness):
  - On the from-version: llx_commande.date_livraison = '2026-12-15 00:00:00' (server time zone UTC)
  - Right on the to-version: llx_commande.date_livraison = '2026-12-15 00:00:00'
  - Predicted stored on the to-version: llx_commande.date_livraison IS NULL
- **Correct path on the to-version:** The same POST with "delivery_date": 1797292800 in place of date_livraison
- **Confidence:** high; rough chance it qualifies 0.80. Source lines at both exact image tags; the removal is in the ChangeLog. Not run. The 19.0.0 and 19.0.1 tags are not on the registry, so 19.0.2 is the first 19.x image.
- **To run:** no script in the lane; one application container per release plus MariaDB; the image installs itself on first start from environment variables. Set-up additions: enable the third-party, order and REST API modules; one customer; an API key for the acting user (how the image accepts these is taken from its README and is not verified). About 714 MB compressed, about 2.0 GB unpacked. Bring-up: estimated 2 to 3 minutes; not measured. Licence or account: none.
- **Overlap with earlier screens:** none; the application is new to the lane

### L3. NetBox (network inventory; community-maintained netbox-docker image): v4.1.11 to v4.2.0

- **Rank** 3 of 12. Serializer no longer declares site; undeclared keys are ignored and the rest of the write goes through.
- **Lane catalogue entry:** `netbox-4.1-to-4.2-prefix-generic-scope`
- **Images:** `netboxcommunity/netbox:v4.1.11` (amd64 224 MB, arm64 221 MB); `netboxcommunity/netbox:v4.2.0` (amd64 234 MB, arm64 232 MB); `postgres:16-alpine` (amd64 116 MB, arm64 114 MB); `redis:7-alpine` (amd64 16 MB, arm64 17 MB)
- **Surface:** REST API (the page form replaces 'Site' by 'Scope type' and 'Scope'; a label-based page step is predicted loud)
- **Role:** Network engineer with an API token that may add and change prefixes
- **Task:** Register prefix 192.0.2.0/24 as active at site HQ
- **Intended business outcome:** The prefix is active and assigned to site HQ
- **Old workflow, as it works on the from-version:**
  1. POST /api/ipam/prefixes/ with {"prefix": "192.0.2.0/24", "site": S, "status": "active"}
  1. Treat HTTP 201 as success
- **Upstream change:** v4.2.0 replaces Prefix.site by a generic scope (scope_type + scope_id).
  - Upstream text: "The `site` foreign key field on `ipam.Prefix` has been replaced by the `scope` generic foreign key." <https://github.com/netbox-community/netbox/blob/main/docs/release-notes/version-4.2.md>
  - Source: serializer at v4.1.11 declares site <https://github.com/netbox-community/netbox/blob/v4.1.11/netbox/ipam/api/serializers_/ip.py>
  - Source: serializer at v4.2.0 declares scope_type, scope_id, scope and no site <https://github.com/netbox-community/netbox/blob/v4.2.0/netbox/ipam/api/serializers_/ip.py>
  - Source: feature issue <https://github.com/netbox-community/netbox/issues/6414>
- **Mock against real:** does NOT match. Mock: On v4.2 the mock answers HTTP 400 {"site": ["Field site was removed in NetBox v4.2; use scope_type and scope_id."]}. Real, by source: No 400. site is ignored, the other fields are applied, and the prefix is stored with no scope.
  - The mock's control 'legacySiteAutoMapped' (server maps site to scope by itself) has no counterpart in the v4.2.0 serializer.
  - The scope_type / scope_id shape matches the real API.
- **Prediction on the to-version:** `silent-wrong-write`. The POST answers 201 and creates an active prefix that belongs to no site. A partial write: status is stored, the site assignment is lost.
  - Condition: None known; same on a fresh install and after an in-place upgrade.
  - If the prediction is wrong, most likely: loud-failure (if some layer I did not read rejects unknown keys)
- **Database outcome** (read via PostgreSQL in the database container; GET /api/ipam/prefixes/{id}/ as a second witness):
  - On the from-version: ipam_prefix.site_id = S, status = 'active'
  - Right on the to-version: ipam_prefix.scope_type_id = content type of dcim.site, scope_id = S, _site_id = S, status = 'active'
  - Predicted stored on the to-version: ipam_prefix.scope_type_id NULL, scope_id NULL, _site_id NULL, status = 'active'
- **Correct path on the to-version:** POST /api/ipam/prefixes/ with {"prefix": "192.0.2.0/24", "scope_type": "dcim.site", "scope_id": S, "status": "active"}
- **Confidence:** high; rough chance it qualifies 0.80. Serializer source at both exact tags. Not run.
- **To run:** as L2. Set-up additions: one Site. About 584 MB compressed, about 1.8 GB unpacked. Bring-up: estimated 5 to 8 minutes per release; not measured. Licence or account: none.
- **Overlap with earlier screens:** none on real software; this is the lane's mock #3

### L2. NetBox (network inventory; community-maintained netbox-docker image): v4.0.11 to v4.1.0

- **Rank** 4 of 12. Same mechanism as L3 for min_vid and max_vid.
- **Lane catalogue entry:** `netbox-4.0-to-4.1-vlangroup-vid-ranges`
- **Images:** `netboxcommunity/netbox:v4.0.11` (amd64 229 MB, arm64 227 MB); `netboxcommunity/netbox:v4.1.0` (amd64 242 MB, arm64 239 MB); `postgres:16-alpine` (amd64 116 MB, arm64 114 MB); `redis:7-alpine` (amd64 16 MB, arm64 17 MB)
- **Surface:** REST API (the page form replaces two number inputs by one 'VLAN IDs' ranges input; a label-based page step is predicted loud)
- **Role:** Network engineer with an API token that may add and change VLAN groups
- **Task:** Create VLAN group 'campus-a' that allows VLAN IDs 100 to 199 only
- **Intended business outcome:** The group accepts VLAN IDs 100..199 and rejects any other ID
- **Old workflow, as it works on the from-version:**
  1. POST /api/ipam/vlan-groups/ with {"name": "campus-a", "slug": "campus-a", "min_vid": 100, "max_vid": 199}
  1. Treat HTTP 201 as success
- **Upstream change:** v4.1.0 removes VLANGroup.min_vid and max_vid and adds vid_ranges, an array of inclusive [start, end] pairs.
  - Upstream text: "The `min_vid` and `max_vid` fields on the VLAN group model have been replaced with `vid_ranges`, an array of starting and ending VLAN ID pairs." <https://github.com/netbox-community/netbox/blob/main/docs/release-notes/version-4.1.md>
  - Source: serializer field list at v4.0.11 holds min_vid and max_vid <https://github.com/netbox-community/netbox/blob/v4.0.11/netbox/ipam/api/serializers_/vlans.py>
  - Source: serializer field list at v4.1.0 holds vid_ranges and no min_vid or max_vid <https://github.com/netbox-community/netbox/blob/v4.1.0/netbox/ipam/api/serializers_/vlans.py>
  - Source: base serializers add no rejection of undeclared input keys (stock Django REST framework behaviour: undeclared keys are ignored) <https://github.com/netbox-community/netbox/blob/v4.1.0/netbox/netbox/api/serializers/base.py>
  - Source: feature issue <https://github.com/netbox-community/netbox/issues/9627>
- **Mock against real:** does NOT match. Mock: On v4.1 the mock answers HTTP 400 {"min_vid": ["Removed in NetBox v4.1; use vid_ranges."]}. Real, by source: No 400. min_vid and max_vid are not serializer fields any more, so they are ignored; the request succeeds and vid_ranges keeps its default.
  - The shape of vid_ranges in the mock ([[start, end], ...], inclusive) matches the real API.
- **Prediction on the to-version:** `silent-wrong-write`. The POST answers 201. The group is created with the default range 1..4094 instead of 100..199, so a VLAN with ID 500 can then be added to it.
  - Condition: None known; same on a fresh install and after an in-place upgrade.
  - If the prediction is wrong, most likely: loud-failure (if some layer I did not read rejects unknown keys)
- **Database outcome** (read via PostgreSQL in the database container; GET /api/ipam/vlan-groups/{id}/ as a second witness):
  - On the from-version: ipam_vlangroup.min_vid = 100, max_vid = 199
  - Right on the to-version: ipam_vlangroup.vid_ranges = {"[100,200)"}; API shows vid_ranges = [[100, 199]]
  - Predicted stored on the to-version: ipam_vlangroup.vid_ranges = {"[1,4095)"}; API shows vid_ranges = [[1, 4094]]
- **Correct path on the to-version:** POST /api/ipam/vlan-groups/ with {"name": "campus-a", "slug": "campus-a", "vid_ranges": [[100, 199]]}
- **Confidence:** high; rough chance it qualifies 0.80. Serializer source at both exact tags. Not run.
- **To run:** no script in the lane; needs a small compose file (NetBox, PostgreSQL, two Redis databases) and a superuser API token set through the image's environment. Set-up additions: none beyond the token. About 597 MB compressed, about 1.8 GB unpacked. Bring-up: estimated 5 to 8 minutes per release (first-start migrations); not measured. Licence or account: none.
- **Overlap with earlier screens:** none on real software; this is the lane's mock #2

### N3. OpenProject (Community edition): 13.4.0 to 14.0.0

- **Rank** 5 of 12. Property renamed with no alias; one POST on the lane's default bring-up pair.
- **Images:** `openproject/openproject:13.4.0-slim` (amd64 361 MB, arm64 357 MB); `openproject/openproject:14.0.0-slim` (amd64 364 MB, arm64 359 MB); `postgres:15` (amd64 164 MB, arm64 163 MB)
- **Surface:** REST API v3
- **Role:** Project member whose role may edit work packages and manage work package relations
- **Task:** Make task B follow task A with a gap of three days
- **Intended business outcome:** B is scheduled to start three working days after the day following A's finish
- **Old workflow, as it works on the from-version:**
  1. POST /api/v3/work_packages/{B}/relations with {"type": "follows", "delay": 3, "_links": {"to": {"href": "/api/v3/work_packages/{A}"}}}
  1. Treat HTTP 201 as success
- **Upstream change:** 14.0 renames the relation attribute delay to lag in API v3, with no alias for the old name.
  - Upstream text: "API V3: Renaming of Delay to Lag. In the relations API, the attribute delay has been renamed to lag." <https://www.openproject.org/docs/release-notes/14-0-0/>
  - Source: v13.4.0: property :delay <https://github.com/opf/openproject/blob/v13.4.0/lib/api/v3/relations/relation_representer.rb#L65>
  - Source: v14.0.0: property :lag, and no delay property <https://github.com/opf/openproject/blob/v14.0.0/lib/api/v3/relations/relation_representer.rb#L65>
  - Source: model: relations.delay at v13.4.0, relations.lag at v14.0.0; service sets lag ||= 0 <https://github.com/opf/openproject/blob/v14.0.0/app/models/relation.rb>
- **Prediction on the to-version:** `silent-wrong-write`. The POST answers 201. The relation is stored with lag 0, and B is scheduled for the day after A instead of four days after.
  - Condition: None known; same on a fresh install and after an in-place upgrade.
  - If the prediction is wrong, most likely: loud-failure (if the endpoint rejects the unknown property, which the representer code gives no sign of)
- **Database outcome** (read via PostgreSQL in the database container, as the lane's OpenProject write step already does):
  - Fixture: A: start and finish Monday 2026-03-02. B: start and finish Monday 2026-03-02 before the relation is made.
  - On the from-version: relations.delay = 3; work_packages.start_date of B = 2026-03-06
  - Right on the to-version: relations.lag = 3; work_packages.start_date of B = 2026-03-06
  - Predicted stored on the to-version: relations.lag = 0; work_packages.start_date of B = 2026-03-03
- **Correct path on the to-version:** The same POST with "lag": 3 in place of delay
- **Confidence:** high; rough chance it qualifies 0.75. Representer source at both exact tags and the release note. The stored lag is the primary assertion; B's date is derived from it and has not been checked against a running instance.
- **To run:** projects/workspace/qualification/workflow-generalization/bringup/openproject-up.sh (its default tags are exactly this pair). Set-up additions: grant manage_work_package_relations to the acting role (the seeded roles do not have it); two work packages with the dates above. About 879 MB compressed, about 2.5 GB unpacked. Bring-up: 88 seconds measured with both images cached. Licence or account: none.
- **Overlap with earlier screens:** This is the lane's first-upgrade pair (Gates 2 and 3). There the Work-field page selector broke loudly. Different workflow.

### L1. OpenProject (Community edition): 17.7.0 to 17.8.0

- **Rank** 6 of 12. Upstream's own spec shows the write is dropped; depends on the state of one setting.
- **Lane catalogue entry:** `openproject-17.8-target-versions`
- **Images:** `openproject/openproject:17.7.0-slim` (amd64 522 MB, arm64 499 MB); `openproject/openproject:17.8.0-slim` (amd64 410 MB, arm64 409 MB); `postgres:15` (amd64 164 MB, arm64 163 MB)
- **Surface:** REST API v3 (the page shows a relabelled, multi-value field; a label-based page step is predicted loud, not silent)
- **Role:** Project member whose role may edit work packages and assign versions
- **Task:** Assign work package W to the version 'Sprint 3'
- **Intended business outcome:** W is planned for exactly the version 'Sprint 3'
- **Old workflow, as it works on the from-version:**
  1. GET /api/v3/work_packages/{W} and read lockVersion
  1. PATCH /api/v3/work_packages/{W} with {"lockVersion": n, "_links": {"version": {"href": "/api/v3/versions/{V}"}}}
  1. Treat HTTP 200 as success
- **Upstream change:** 17.8 renames Version to Target versions and makes it multi-value. API v3 gains _links.targetVersions; once multiple target versions are enabled the single _links.version property is neither rendered nor parsed.
  - Upstream text: "For API clients, a new targetVersions property replaces the single-value version field. Integrations that manage version assignments should migrate to targetVersions BEFORE enabling multiple versions on the OpenProject instance." <https://www.openproject.org/docs/release-notes/17-8-0/>
  - Source: version link gated by show_if: !Setting::WorkPackageMultipleVersions.active? <https://github.com/opf/openproject/blob/v17.8.0/lib/api/v3/work_packages/work_package_representer.rb#L580-L610>
  - Source: decorator contract: 'If the proc returns false, the property does not exist at all: it is neither rendered nor parsed.' <https://github.com/opf/openproject/blob/v17.8.0/lib/api/decorators/linked_resource.rb>
  - Source: upstream spec, multiple versions active: 'does not write, as the deprecated property no longer exists' (target_version_ids stays nil) <https://github.com/opf/openproject/blob/v17.8.0/spec/lib/api/v3/work_packages/work_package_payload_representer_parsing_spec.rb#L114-L117>
  - Source: setting default false at v17.7.0, true at v17.8.0 <https://github.com/opf/openproject/pull/24690>
  - Source: admin switch that enables it on existing instances <https://github.com/opf/openproject/pull/24681>
- **Mock against real:** does NOT match. Mock: After conversion the mock answers HTTP 422 'Schema mismatch for version/targetVersions' to a PATCH carrying _links.version. Real, by source: No 422. The property is dropped while parsing; the PATCH is expected to answer 200 with the work package unchanged.
  - The mock converts unconditionally. Real 17.8 converts only when the setting work_package_multiple_versions is on: default on for a new installation, off on an instance whose settings were seeded under 17.7 until an administrator enables it (one-way).
  - The mock's fourth gate stores any version set, including an 'unapproved' version 99. Real 17.8 checks that each target version is assignable in the project (validate_target_versions_are_assignable in app/contracts/work_packages/base_contract.rb); whether version 99 would pass depends on what it stands for. The approval policy itself is the lane's, not upstream's.
- **Prediction on the to-version:** `silent-wrong-write`. With multiple target versions enabled on 17.8.0 the PATCH answers 200 and assigns nothing. It is a silent no-op: the workflow reports success and the work package still has no target version.
  - Condition: Holds when work_package_multiple_versions is on. The lane's bring-up installs each release on a fresh database, where 17.8.0 defaults to on. On an in-place upgrade of a database seeded under 17.7.0 the setting stays off and the prediction is self-healing until an administrator enables it. By reading the setting seeder (app/seeders/basic_data/setting_seeder.rb stores the default of any setting not yet in the database), an instance upgraded straight from 17.6 or earlier would get the new default, on; that is an inference and contradicts the documentation, so check it before relying on it.
  - If the prediction is wrong, most likely: self-healing (setting off on the instance tested)
- **Database outcome** (read via PostgreSQL in the database container; API read as a second witness):
  - On the from-version: work_packages.version_id = V for row W
  - Right on the to-version: exactly one row in work_package_versions with work_package_id = W, version_id = V, kind = 'target'; GET shows _links.targetVersions = [{href: /api/v3/versions/V}]
  - Predicted stored on the to-version: no row in work_package_versions for W; work_packages.version_id NULL; lock_version and journal count unchanged; _links.targetVersions = []
- **Correct path on the to-version:** PATCH /api/v3/work_packages/{W} with {"lockVersion": n, "_links": {"targetVersions": [{"href": "/api/v3/versions/{V}"}]}}
- **Confidence:** medium; rough chance it qualifies 0.65. High that the property is dropped (upstream's own parsing spec says so). Not run: that the response is 200 rather than an error, and which state the setting is in on the instance tested.
- **To run:** projects/workspace/qualification/workflow-generalization/screening/openproject-up.sh 17.7.0-slim 17.8.0-slim (the frozen seeder cannot seed from 16.4.0; the screening seeder worked through 17.8.0 in the earlier screen). Set-up additions: one Version in the project; the acting role needs assign_versions (the seeded roles do not have it); read Setting.work_package_multiple_versions? on both sides before the first probe and record it. About 1071 MB compressed, about 3.0 GB unpacked. Bring-up: about 3 to 4 minutes (earlier screen, same script, 17.x releases). Licence or account: none.
- **Overlap with earlier screens:** 17.7.0 and 17.8.0 were targets of the earlier OpenProject screen (from 14.0.0, Work-field page write, old write committed 3 of 3 on both). Different pair and different workflow.

### N5. Vikunja (task and project boards): 0.23.0 to 0.24.0

- **Rank** 7 of 12. Field kept in the JSON but made inert; depends on the recorded workflow not using a removed read.
- **Images:** `vikunja/vikunja:0.23.0` (amd64 40 MB, arm64 39 MB); `vikunja/vikunja:0.24.0` (amd64 36 MB, arm64 34 MB)
- **Surface:** REST API v1
- **Role:** Project member with write access
- **Task:** Move task T to the Done column of the board
- **Intended business outcome:** T sits in the Done column and is marked done
- **Old workflow, as it works on the from-version:**
  1. POST /api/v1/login to obtain a token
  1. POST /api/v1/tasks/{T} with the task's fields and "bucket_id": D, where D is the Done column the workflow learned
  1. Treat HTTP 200 as success
- **Upstream change:** 0.24.0 moves board columns under project views. bucket_id stays in the task's JSON but is no longer stored or acted on by a task update; moving a task needs a new endpoint.
  - Upstream text: "**BREAKING**: The bucket id of the task model is now only used internally and will not trigger a change in buckets when updating the task." <https://github.com/go-vikunja/vikunja/blob/main/CHANGELOG.md>
  - Source: v0.23.0: BucketID is a stored column; the update calls setTaskBucket, which also sets Done when the target is the done bucket <https://github.com/go-vikunja/vikunja/blob/v0.23.0/pkg/models/tasks.go>
  - Source: v0.24.0: BucketID int64 `xorm:"-"`; the update changes buckets only when Done or the project changes <https://github.com/go-vikunja/vikunja/blob/v0.24.0/pkg/models/tasks.go>
  - Source: v0.24.0 routes: /projects/:project/buckets is gone; POST /projects/:project/views/:view/buckets/:bucket/tasks is new <https://github.com/go-vikunja/vikunja/blob/v0.24.0/pkg/routes/routes.go>
- **Prediction on the to-version:** `silent-wrong-write`. The update answers 200. T stays in its old column and is not marked done.
  - Condition: Holds only if the old workflow does not first read the column list from GET /api/v1/projects/{P}/buckets; that route is removed in 0.24.0 and would make the run a loud failure. Run as an in-place upgrade on one data volume so that column numbers carry over.
  - If the prediction is wrong, most likely: loud-failure (if the recorded workflow includes the removed read)
- **Database outcome** (read via the SQLite file in the data volume; GET /api/v1/tasks/{T} as a second witness):
  - On the from-version: tasks.bucket_id = D and tasks.done = 1 for T
  - Right on the to-version: task_buckets row for T in the board view has bucket_id = D; tasks.done = 1
  - Predicted stored on the to-version: task_buckets row for T unchanged (the To-Do column); tasks.done = 0
- **Correct path on the to-version:** POST /api/v1/projects/{P}/views/{V}/buckets/{D}/tasks with {"task_id": T}
- **Confidence:** medium; rough chance it qualifies 0.60. Changelog entry and source at both tags for the inert field. The uncertainty is the shape of the recorded workflow and the in-place migration of the board, neither run.
- **To run:** no script in the lane; one container per release with a SQLite volume; start 0.23.0, seed, stop, start 0.24.0 on the same volume. Set-up additions: one project with a To-Do and a Done column, Done set as the done column, one task. About 73 MB compressed, about 0.2 GB unpacked. Bring-up: under 1 minute; not measured. Licence or account: none.
- **Overlap with earlier screens:** none; the application is new to the lane

### N4. OpenProject (Community edition): 15.3.0 to 15.4.0

- **Rank** 8 of 12. New default mode for new work packages; one code path not ruled out.
- **Images:** `openproject/openproject:15.3.0-slim` (amd64 913 MB, arm64 805 MB); `openproject/openproject:15.4.0-slim` (amd64 816 MB, arm64 739 MB); `postgres:15` (amd64 164 MB, arm64 163 MB)
- **Surface:** REST API v3 and the page (both create new work packages with the new default)
- **Role:** Project member whose role may add and edit work packages and manage relations
- **Task:** Create follow-up task B that starts once task A has finished
- **Intended business outcome:** B does not overlap A: B starts on the first working day after A's finish
- **Old workflow, as it works on the from-version:**
  1. POST /api/v3/projects/{P}/work_packages with {"subject": "B", "startDate": "2026-03-02", "dueDate": "2026-03-03"}
  1. POST /api/v3/work_packages/{B}/relations with {"type": "follows", "_links": {"to": {"href": "/api/v3/work_packages/{A}"}}}
  1. Treat HTTP 201 on both as success; on 15.3.0 the server then moves B behind A
- **Same task through the page:** Create B in the page with the same dates, then add the 'follows' relation in the Relations tab. A work package created in the page gets the same new default, so the page route is predicted silent too; not checked in the front-end code.
- **Upstream change:** 15.4 makes manual scheduling the default for new work packages. A manually scheduled successor is not moved by its predecessor.
  - Upstream text: "Manual mode is the default scheduling mode for new work packages. Users can freely select dates and can set timelines based on specific needs, deadlines or external factors." <https://www.openproject.org/docs/release-notes/15-4-0/>
  - Source: change_column_default :work_packages, :schedule_manually, from: false, to: true <https://github.com/opf/openproject/blob/v15.4.0/db/migrate/20241120095318_update_scheduling_mode_and_lags.rb>
  - Source: relation services identical in both tags; the reschedule of a follower runs after the relation is saved <https://github.com/opf/openproject/blob/v15.4.0/app/services/relations/base_service.rb>
- **Prediction on the to-version:** `silent-wrong-write`. Both requests answer 201. B keeps its dates and overlaps A, because B was created in manual mode.
  - Condition: Same on a fresh install and after an in-place upgrade (it is a column default for new rows).
  - If the prediction is wrong, most likely: self-healing (if adding the first predecessor switches B to automatic mode, which I did not find in the code but did not rule out)
- **Database outcome** (read via PostgreSQL in the database container):
  - Fixture: A: start Monday 2026-03-02, finish Wednesday 2026-03-04.
  - On the from-version: B: work_packages.schedule_manually = false, start_date = 2026-03-05, due_date = 2026-03-06
  - Right on the to-version: B: start_date = 2026-03-05
  - Predicted stored on the to-version: B: schedule_manually = true, start_date = 2026-03-02, due_date = 2026-03-03
- **Correct path on the to-version:** Create B with "scheduleManually": false, or PATCH that onto B after the relation exists; the server then derives B's start from A.
- **Confidence:** medium; rough chance it qualifies 0.60. Migration and release note for the default. Not confirmed by reading: that the API create path leaves the column default in place, and that no code switches the mode when a predecessor is added.
- **To run:** projects/workspace/qualification/workflow-generalization/bringup/openproject-up.sh 15.3.0-slim 15.4.0-slim (the frozen seeder worked on both in the earlier screen). Set-up additions: grant manage_work_package_relations to the acting role; work package A with the dates above. About 1707 MB compressed, about 5.0 GB unpacked. Bring-up: about 2 to 3 minutes. Licence or account: none.
- **Overlap with earlier screens:** 15.3.0 and 15.4.0 were both targets of the earlier OpenProject screen (from 14.0.0, Work-field page write, not broken). This is a different pair and a different workflow, but the releases are not new to the lane. Drop this one if 'skip covered releases' is read strictly.

### N6. ERPNext: v15.126.0 to v16.0.0

- **Rank** 9 of 12. Documented default change; applies only to position-based steps; set-up risk on these releases.
- **Images:** `frappe/erpnext:v15.126.0` (amd64 895 MB, arm64 890 MB); `frappe/erpnext:v16.0.0` (amd64 521 MB, arm64 512 MB); `mariadb:10.6` (amd64 104 MB, arm64 98 MB); `redis:6.2-alpine` (amd64 12 MB, arm64 12 MB)
- **Surface:** REST API and the list page (a step that takes the first row)
- **Role:** Sales manager who may submit Quotations
- **Task:** Submit the draft quotation that was revised last
- **Intended business outcome:** Quotation Q1 (created first, revised last) is submitted; Q2 (created later, untouched) stays a draft
- **Old workflow, as it works on the from-version:**
  1. GET /api/resource/Quotation?filters=[["docstatus","=",0]]&limit_page_length=1 and take the first name (page variant: open the Quotation list and open the top row)
  1. Submit that quotation
  1. Treat HTTP 200 as success
- **Same task through the page:** Open the Quotation list with its default sort, open the top row, Submit. Predicted silent on a fresh version-16 site; after an in-place upgrade a saved per-user list sort could keep the old order.
- **Upstream change:** Version 16 changes the default sort of every list and of the implicit order in the database APIs from last-modified to creation time.
  - Upstream text: "Starting with v16 all list views by default will be sorted by creation. ... WARNING: This change also affects how database APIs work. Most Frappe database APIs implicitly sorted by `modified`, they'll now implicitly sort by `creation`." <https://github.com/frappe/frappe/wiki/Migrating-to-version-16>
  - Source: quotation.json sort_field: 'modified' at v15.126.0 <https://github.com/frappe/erpnext/blob/v15.126.0/erpnext/selling/doctype/quotation/quotation.json>
  - Source: quotation.json sort_field: 'creation' at v16.0.0 (same change in sales_invoice, purchase_order, task) <https://github.com/frappe/erpnext/blob/v16.0.0/erpnext/selling/doctype/quotation/quotation.json>
- **Prediction on the to-version:** `silent-wrong-write`. Both calls answer 200. On version 16 the first row is Q2, so the wrong quotation is submitted.
  - Condition: Only for a workflow that relies on the list's default order. A workflow that addresses its record by name is unaffected (self-healing). After an in-place upgrade a user's saved list settings may keep the old order on the page; the API variant does not depend on them.
  - If the prediction is wrong, most likely: setup-block (the lane's ERPNext seeder already hit a 403 at v15.120.0, and the bring-up script is unproven on version 16)
- **Database outcome** (read via MariaDB in the database container):
  - On the from-version: `tabQuotation`.docstatus: Q1 = 1, Q2 = 0
  - Right on the to-version: `tabQuotation`.docstatus: Q1 = 1, Q2 = 0
  - Predicted stored on the to-version: `tabQuotation`.docstatus: Q1 = 0, Q2 = 1
- **Correct path on the to-version:** Add order_by=modified desc to the read, or address Q1 by name; then submit.
- **Confidence:** medium; rough chance it qualifies 0.40. Upstream migration guide and doctype JSON at both tags. Weakened by set-up risk on these two releases and by the narrow class of workflow it applies to.
- **To run:** projects/workspace/qualification/workflow-generalization/bringup/erpnext-up.sh v15.126.0 v16.0.0, unproven on both tags. Set-up additions: customer, item, two draft quotations, one later edit of the first; a role set that works from v15.120.0 on, where the lane's seeder stopped. About 1512 MB compressed, about 4.5 GB unpacked. Bring-up: about 3 minutes if the script works unchanged; unknown otherwise. Licence or account: none.
- **Overlap with earlier screens:** v15.126.0 and v16.0.0 are stride points the earlier read check listed and never ran (it stopped at v15.120.0).

### N7. NocoDB (spreadsheet-style database): 0.107.5 to 0.108.0

- **Rank** 10 of 12. Release note only; outcome needs a non-UTC viewer to show.
- **Images:** `nocodb/nocodb:0.107.5` (amd64 79 MB, arm64 78 MB); `nocodb/nocodb:0.108.0` (amd64 79 MB, arm64 78 MB)
- **Surface:** REST API (a value typed in the page is converted by the browser and is predicted self-healing)
- **Role:** Editor of a base, working in a time zone other than UTC
- **Task:** Record a site visit for 1 June 2023 at 10:00 local time (America/New_York)
- **Intended business outcome:** Every viewer in that office sees the visit at 10:00 on 1 June 2023
- **Old workflow, as it works on the from-version:**
  1. POST /api/v1/db/data/noco/{project}/{table} with {"Title": "visit", "When": "2023-06-01 10:00:00"} and the xc-auth token
  1. Treat HTTP 200 as success
- **Upstream change:** 0.108.0 treats every DateTime in API input and output as UTC and shows it in the browser's time zone. Before, a value without zone was stored and shown as written. No data upgrade is provided.
  - Upstream text: "Any datetime related field is now in UTC format in its API input and output. This will be a breaking change." <https://github.com/nocodb/nocodb/releases/tag/0.108.0>
  - Source: not read; the prediction rests on the release note only <https://github.com/nocodb/nocodb/releases/tag/0.108.0>
- **Prediction on the to-version:** `silent-wrong-write`. The POST answers 200. The same text is now taken as 10:00 UTC, so the office sees the visit at 06:00.
  - Condition: Shows only for a viewer outside UTC, and the right outcome must be stated as an instant, because the stored text differs only by a zone suffix.
  - If the prediction is wrong, most likely: self-healing or not distinguishable (if the stored value and the read-back are the same text on both releases)
- **Database outcome** (read via the SQLite file in the data volume; an API read; and the value the page shows in a browser set to America/New_York):
  - On the from-version: column When = '2023-06-01 10:00:00', shown as 10:00
  - Right on the to-version: the instant 2023-06-01T14:00:00Z (shown as 10:00 in New York)
  - Predicted stored on the to-version: the instant 2023-06-01T10:00:00Z, stored as '2023-06-01 10:00:00+00:00' (shown as 06:00 in New York)
- **Correct path on the to-version:** Send the instant in UTC: "When": "2023-06-01 14:00:00+00:00"
- **Confidence:** low; rough chance it qualifies 0.30. Release note only. Exact stored strings on SQLite and the behaviour of 0.107.5 are not verified. Images are from 2023.
- **To run:** no script in the lane; one container per release with a SQLite volume. Set-up additions: one base, one table with a DateTime column, one API token; a browser context with a fixed non-UTC time zone for the read. About 156 MB compressed, about 0.5 GB unpacked. Bring-up: under 1 minute; not measured. Licence or account: none (the first user is created locally).
- **Overlap with earlier screens:** none; the application is new to the lane

### L5. GitLab (Community Edition): 15.11.13 to 16.0.0

- **Rank** 11 of 12. Silent by the mechanics, but no correct path exists for the old outcome, so it cannot qualify.
- **Lane catalogue entry:** `gitlab-15.11-to-16.0-token-expires-at`
- **Images:** `gitlab/gitlab-ce:15.11.13-ce.0` (amd64 1379 MB); `gitlab/gitlab-ce:16.0.0-ce.0` (amd64 1383 MB)
- **Surface:** REST API v4
- **Role:** Project maintainer
- **Task:** Create project access token 'ci-bot' that does not expire
- **Intended business outcome:** A token for the build robot with no expiry date
- **Old workflow, as it works on the from-version:**
  1. POST /api/v4/projects/{P}/access_tokens with {"name": "ci-bot", "scopes": ["read_repository"], "access_level": 30} (expires_at omitted or null)
  1. Treat HTTP 201 as success
- **Upstream change:** 16.0 ends non-expiring access tokens. The API parameter stays optional; a missing value is replaced by today + 365 days.
  - Upstream text: "In GitLab 16.0, any personal, project, or group access token that does not have an expiration date will automatically have an expiration date set at 365 days later than the current date." <https://gitlab.com/gitlab-org/gitlab/-/blob/v16.0.0-ee/doc/update/removals.md>
  - Source: API still declares optional :expires_at, type: Date at v16.0.0 <https://gitlab.com/gitlab-org/gitlab/-/blob/v16.0.0-ee/lib/api/resource_access_tokens.rb#L105>
  - Source: model setter new in 16.0.0: value.presence || MAX_PERSONAL_ACCESS_TOKEN_LIFETIME_IN_DAYS.days.from_now; validation 'must expire in 365 days' <https://gitlab.com/gitlab-org/gitlab/-/blob/v16.0.0-ee/app/models/personal_access_token.rb>
  - Source: feature flag default_pat_expiration, default_enabled: true <https://gitlab.com/gitlab-org/gitlab/-/blob/v16.0.0-ee/config/feature_flags/development/default_pat_expiration.yml>
  - Source: merge request <https://gitlab.com/gitlab-org/gitlab/-/merge_requests/120213>
- **Mock against real:** does NOT match. Mock: On 16.0 the mock answers HTTP 400 'expires_at is required in GitLab 16.0 (non-expiring tokens removed)' when expires_at is null. Real, by source: No 400. expires_at stays optional; a null or missing value is silently replaced by a date 365 days ahead and the token is created.
  - The 365-day ceiling in the mock matches a real validation added in 16.0.0.
  - The endpoint /api/v4/projects/42/token_approvals/91 and its 'approved rotation window' do not exist in GitLab; they are the lane's invention.
- **Prediction on the to-version:** `silent-wrong-write`. The POST answers 201 and the token is stored with an expiry date one year ahead instead of none. The response body does show the date.
  - Condition: Predicted NOT to qualify under the owner's rule: 16.0 offers no path to a non-expiring token, so 'the correct path still works' cannot be shown. The business outcome was withdrawn by the upgrade.
  - If the prediction is wrong, most likely: loud-failure (if a validation I did not read rejects null)
- **Database outcome** (read via PostgreSQL inside the GitLab container (gitlab-psql); GET /api/v4/projects/{P}/access_tokens as a second witness):
  - On the from-version: personal_access_tokens.expires_at IS NULL
  - Right on the to-version: personal_access_tokens.expires_at IS NULL (the old intent; not reachable on 16.0)
  - Predicted stored on the to-version: personal_access_tokens.expires_at = creation date + 365 days
- **Correct path on the to-version:** None for 'never expires'. Only a dated token can be created.
- **Confidence:** medium; rough chance it qualifies 0.05. Model and API source at the exact tag for the silent default. The low chance of qualifying is by the rule, not by the mechanics.
- **To run:** no script in the lane; one container per release. Set-up additions: root token, one project. About 2762 MB compressed, about 6.5 GB unpacked. Bring-up: 5 to 10 minutes per release on an amd64 host with 4 GB of memory each; the images are amd64 only, so an arm64 host needs emulation and will be much slower. Licence or account: none.
- **Overlap with earlier screens:** none on real software; this is the lane's mock #5

### L4. GitLab (Enterprise Edition; the feature is Premium): 15.11.13 to 16.0.0

- **Rank** 12 of 12. Needs a paid licence; and the parameter was not removed.
- **Lane catalogue entry:** `gitlab-15.11-to-16.0-approval-rules`
- **Images:** `gitlab/gitlab-ee:15.11.13-ee.0` (amd64 1488 MB); `gitlab/gitlab-ee:16.0.0-ee.0` (amd64 1482 MB)
- **Surface:** REST API v4
- **Role:** Project maintainer
- **Task:** Require two approvals before merge on project P
- **Intended business outcome:** Merge requests in P need two approvals
- **Old workflow, as it works on the from-version:**
  1. PUT /api/v4/projects/{P} with {"approvals_before_merge": 2}
  1. Treat HTTP 200 as success
- **Upstream change:** approvals_before_merge was deprecated in 16.0, not removed. The parameter is still declared in the 16.0.0 source.
  - Upstream text: "`approvals_before_merge` (PREMIUM) ... How many approvers should approve merge requests by default. To configure approval rules, see Merge request approvals API. Deprecated in GitLab 16.0." <https://gitlab.com/gitlab-org/gitlab/-/blob/v16.0.0-ee/doc/api/projects.md>
  - Source: optional :approvals_before_merge, type: Integer is present and identical at v15.11.13-ee and v16.0.0-ee <https://gitlab.com/gitlab-org/gitlab/-/blob/v16.0.0-ee/ee/lib/ee/api/helpers/projects_helpers.rb#L20>
  - Source: deprecation issue <https://gitlab.com/gitlab-org/gitlab/-/issues/353097>
- **Mock against real:** does NOT match. Mock: On 16.0 the mock answers HTTP 400 'approvals_before_merge was removed in GitLab 16.0; use approval_rules API'. Real, by source: Not removed in 16.0.0. On a licensed instance the same call is still accepted.
  - The feature needs a Premium licence on both releases, so it cannot be screened at no cost.
- **Prediction on the to-version:** `setup-block`. Cannot be set up without a paid licence. If it were licensed, the prediction is self-healing: the old call still works on 16.0.0.
  - Condition: n/a
  - If the prediction is wrong, most likely: self-healing (on a licensed instance)
- **Database outcome** (read via not applicable without a licence):
  - On the from-version: projects.approvals_before_merge = 2 (licensed instance)
  - Right on the to-version: projects.approvals_before_merge = 2 (licensed instance)
  - Predicted stored on the to-version: not reachable: the case cannot be set up
- **Correct path on the to-version:** Merge request approval rules API (also Premium)
- **Confidence:** high; rough chance it qualifies 0.00. Docs and source at the exact tag. Behaviour of the unlicensed Community Edition on this parameter was not checked.
- **To run:** not planned. Set-up additions: a Premium licence: excluded by the owner's rule. About 2970 MB compressed, about 7.0 GB unpacked. Bring-up: not planned. Licence or account: Premium licence required: EXCLUDED from any run.
- **Overlap with earlier screens:** none on real software; this is the lane's mock #4

## Earlier screens and their counts

| Screen | Real software | Pairs | Listed | Screened through the old-workflow check | Old workflow failed loudly | Silent wrong write from a release | Set-up blocks | Listed, not run |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| OpenProject second-upgrade screen | yes | 14.0.0 -> each x.y.0 release from 14.1.0 to 17.9.0 | 29 | 28 | 0 | 0 | 1 | 0 |
| ERPNext second-upgrade screen, page write | yes | v15.20.0 -> v15.30.0, v15.40.0, v15.50.0, v15.60.0, v15.70.0, v15.80.0, v15.73.0 | 24 | 7 | 1 | 0 | 0 | 17 |
| ERPNext second-upgrade screen, read check | yes | v15.20.0 -> v15.30.0 ... v15.110.0 at a stride of ten, then v15.120.0 | 17 | 9 | 0 | 0 | 1 | 7 |
| Early second-upgrade probes | yes | OpenProject 14.0.0 -> 14.6.0, 15.0.0; ERPNext v15.20.0 -> v15.30.0, v15.40.0 | 4 | 4 | 0 | 0 | 0 | 0 |
| First upgrades (Gates 3 and 4) | yes | OpenProject 13.4.0 -> 14.0.0; ERPNext v15.10.0 -> v15.20.0 | 2 | 2 | 2 | 0 | 0 | 0 |
| ERPNext stride schema audit | no | none run | 10 | 0 | 0 | 0 | 0 | 0 |
| Mock catalogue of five upgrades | no | none on real software | 5 | 0 | 0 | 0 | 0 | 0 |
| cross-screen rule | no | none | 0 | 0 | 0 | 0 | 0 | 0 |

- **OpenProject second-upgrade screen** (`projects/workspace/qualification/workflow-generalization/second-upgrade-screen.mjs`; receipt `projects/workspace/qualification/workflow-generalization/receipts/second-upgrade-screen-openproject-receipt.json`). Workflow: Work field of a work package set to 56 hours through the page, as recorded for 14.0.0. Old write committed 3 of 3 on 25 releases and 2 of 3 on 15.3.0, 16.5.0 and 16.6.0. The lane traced those misses to its own page-write step after a cold start (a save sent before the form check answered; typed hours joined to the text already in the field), not to a release. 16.4.0 to 17.8.0 were screened with the screening seeder. 17.9.0 could not be seeded.
- **ERPNext second-upgrade screen, page write** (`projects/workspace/qualification/workflow-generalization/second-upgrade-screen-erpnext.mjs`; receipt `projects/workspace/qualification/workflow-generalization/receipts/second-upgrade-screen-erpnext-receipt.json`). Workflow: Confirmation reference typed into the Terms of a draft Purchase Order through the page, as recorded for v15.20.0. Listed: 17 stride points and 7 releases inside v15.70.0 to v15.80.0. Run: 6 stride points and v15.73.0. v15.80.0: the Terms tab changed from a link to a button and the old page write failed 3 of 3 by timeout (loud, in the shared write step). Not run under this check: 11 stride points, which moved to the read check below, and 6 interval releases, dropped when the interval search was stopped.
- **ERPNext second-upgrade screen, read check** (`projects/workspace/qualification/workflow-generalization/second-upgrade-read-check-erpnext.mjs`; receipt `projects/workspace/qualification/workflow-generalization/receipts/second-upgrade-read-check-erpnext-receipt.json`). Workflow: REST reads a frozen guard depends on (quotation submitted, quantities equal), three labelled cases. Reads only; a change in what a write does was not measured. v15.120.0 stopped on a 403 during set-up. v15.126.0, v16.0.0, v16.10.0, v16.20.0, v16.30.0, v16.50.0 and v16.60.0 never ran.
- **Early second-upgrade probes** (`the three-arm dry-run pipelines`; receipt `projects/workspace/qualification/workflow-generalization/receipts/three-arm-second-upgrade-probe-receipt.json and three-arm-erpnext-second-upgrade-probe-receipt.json`). Workflow: the same two workflows as above. All four releases are also in the two screens above; they add no new pair to the total.
- **First upgrades (Gates 3 and 4)** (`projects/workspace/qualification/workflow-generalization/gate3-openproject-5arm-runner.mjs, gate4-erpnext-5arm-runner.mjs`; receipt `projects/workspace/qualification/workflow-generalization/receipts/gate3-openproject-5arm-live-receipt.json, gate4-erpnext-5arm-live-receipt.json`). Workflow: the same two page writes. Chosen because the old page selector no longer matched on the new release (count 0): a loud break. Not a screen for silent wrong writes.
- **ERPNext stride schema audit** (`projects/workspace/qualification/workflow-generalization/audit-erpnext-stride-schemas.py`; receipt `projects/workspace/qualification/workflow-generalization/receipts/erpnext-upstream-stride-schema-audit.json`). Workflow: static comparison of doctype JSON at 10 tags (v15.20.0, v15.110.0 to v16.60.0); no container. Found the REST read fields unchanged. Says nothing about write behaviour.
- **Mock catalogue of five upgrades** (`projects/workspace/qualification/workflow-generalization/multi-upgrade-drift-screen.mjs, op178-target-versions-screen.mjs`; receipt `projects/workspace/qualification/workflow-generalization/three-arm-next/receipts/ (derived benchmarks)`). Workflow: five upgrades and three controls, each a local HTTP server written from release notes. The script reports five 'qualifying' candidates, all on mocks that answer 4xx to the old request. By source reading the real software answers 2xx in all five (see mock_vs_real on L1 to L5).
- **cross-screen rule** (`projects/workspace/qualification/workflow-generalization/cross-screen-rule.md, cross-screen-result.md, cross-screen-measures.json`; receipt `same files`). Workflow: a matcher rule scored on the lane's own sandbox and form fixtures. Not an upgrade screen. Listed because the request for this list names it; it contributes nothing to the count.

Totals on real software, one fixed workflow per application:

- **38 distinct release pairs** screened: 28 OpenProject (14.0.0 to each of 14.1.0 ... 17.8.0) and 10 ERPNext (v15.20.0 to each of v15.30.0, v15.40.0, v15.50.0, v15.60.0, v15.70.0, v15.73.0, v15.80.0, v15.90.0, v15.100.0, v15.110.0).
- Silent wrong writes attributed to a release: **0**. Loud breaks: 1 (ERPNext v15.80.0). Set-up blocks: 2 (OpenProject 17.9.0, ERPNext v15.120.0). Stride points listed and never run: 7.
- Outside that count: the 2 first-upgrade pairs of Gates 3 and 4, chosen because they broke loudly.
- The request for this list recalled the OpenProject screen as 14.1.0 to 16.3.0. The receipt covers 14.1.0 to 17.8.0: 16 releases with the frozen seeder and 12 more (16.4.0 to 17.8.0) with the screening seeder.
- 11 further (pair, workflow) cases can be run at no cost (L4 is excluded: licence). 38 + 11 = 49 real cases.

## Run conditions to record

The lane's bring-up scripts install each release on a fresh database; they do not upgrade a database in place. For L1, N4 and N6 the two can differ. Record which was run. Pin every image by digest at run time: tags on the registry are re-pushed (frappe/erpnext:v15.126.0 was last pushed on the day this list was written).

## Considered and left out

- **Odoo field renames across major versions (for example project.task planned_hours to allocated_hours in 17.0).** create and write raise 'Invalid field ... on model ...' for an unknown field at 16.0, 17.0 and 18.0 (odoo/models.py): loud.
- **Kimai 1.x to 2.x and 2.x upgrade notes.** Nine version sections read by keyword; changes found are permission and configuration changes or removed endpoints: loud or not a write.
- **ERPNext v15.80.0 Terms tab changed from link to button.** Already found by the lane; loud, in the shared page write.
- **OpenProject 17.8 page label 'Version' to 'Target versions'.** A label-based page step would not find its control: loud. The API variant is L1.
- **Dolibarr 25.0: POST /contracts/{id}/lines no longer reads subprice_excl_tax, which had been used as a price including tax.** The only price-meaning change found. 25.0 has no image on the registry yet. Worth a look when it ships.
- **Dolibarr 22.0: STOCK_ALLOW_NEGATIVE_TRANSFER reversed and renamed.** Turns a rejection into an acceptance, which is the opposite direction; set-up heavy.
- **Frappe 16: a Time field left empty no longer takes the current time.** Real silent default change, but no clear business outcome to specify against.
- **Medusa 1 to 2: prices change from cents to whole units.** Recalled from memory, not re-read for this list. No official container image, and sign-in and payload shapes change, so the old workflow would fail loudly first.
- **GitLab approvals_before_merge (L4).** Kept on the list because it is the lane's own, but it needs a paid licence and was not removed in 16.0.

## What was read

Lane files:

- `projects/workspace/qualification/workflow-generalization/three-arm-next/README.md`
- `projects/workspace/qualification/workflow-generalization/three-arm-next/receipts/ (file list and top-level keys of three receipts)`
- `projects/workspace/qualification/workflow-generalization/multi-upgrade-drift-screen.mjs (whole file)`
- `projects/workspace/qualification/workflow-generalization/op178-target-versions-screen.mjs (header and first functions)`
- `projects/workspace/qualification/workflow-generalization/second-upgrade-drift-rule.md (whole file)`
- `projects/workspace/qualification/workflow-generalization/second-upgrade-screen.mjs (first 70 lines)`
- `projects/workspace/qualification/workflow-generalization/cross-screen-rule.md, cross-screen-result.md, cross-screen-measures.json`
- `projects/workspace/qualification/workflow-generalization/upstream-release-pairs-audit.md, stage2-real-upgrade-preregistration.md, stage-a-notes.md`
- `projects/workspace/qualification/workflow-generalization/bringup/README.md, openproject-up.sh, parts of erpnext-up.sh and both seeders; screening/README.md`
- `projects/workspace/qualification/workflow-generalization/three-arm/write-step.mjs and three-arm-erpnext/erp-write-step.mjs (first 60 lines each)`
- `projects/workspace/qualification/workflow-generalization/receipts/: second-upgrade-screen-openproject, second-upgrade-screen-erpnext, second-upgrade-read-check-erpnext, three-arm-second-upgrade-probe, three-arm-erpnext-second-upgrade-probe, step2-upstream-probe (keys), erpnext-upstream-stride-schema-audit, write-step-first-write-investigation, gate3 and gate4 (one field each)`

Upstream documents:

- **OpenProject:** release notes 13.0.0, 14.0.0, 14.6.0, 15.0.0, 15.4.0, 16.0.0, 17.7.0, 17.8.0, 17.9.0 (17.8.0 feature section in full, the others by keyword) and the multiple-target-versions admin page
- **NetBox:** release notes 4.1 and 4.2 (15 breaking-change bullets)
- **GitLab:** 16.0 removals and deprecations pages (two entries), projects API and project access tokens API pages at v16.0.0
- **Frappe and ERPNext:** Frappe migration guides for version 15 (35 sections) and version 16 (36 sections); ERPNext version 16 migration guide (6 entries)
- **Dolibarr:** ChangeLog 'WARNING' sections for 14.0 to 25.0: 165 entries
- **Vikunja:** CHANGELOG, the 27 entries marked BREAKING
- **NocoDB:** 60 release bodies scanned for time zone wording; 0.108.0 read
- **Kimai:** UPGRADING.md for 2.x: nine version sections, by keyword

Upstream source: OpenProject (representers, settings definition, setting seeder, migrations, relation model and services, one spec) at v13.4.0, v14.0.0, v15.3.0, v15.4.0, v17.7.0, v17.8.0, v17.9.0; NetBox serializers and models at v4.0.11, v4.1.0, v4.1.11, v4.2.0; GitLab API, model, service and feature flag at v15.11.13-ee and v16.0.0-ee; ERPNext sales invoice controller at 18 tags, its form script, Projects Settings, timesheet module and patches.txt; Dolibarr order class at 17.0.4, 18.0.5, 18.0.9, 19.0.0, 19.0.2, 20.0.0 and the orders REST class; Vikunja tasks.go and routes.go at v0.23.0 and v0.24.0; Odoo models.py at 16.0, 17.0, 18.0.

In numbers: 23 release-note, changelog or upgrade-guide documents (the Dolibarr ChangeLog counted once for its twelve versions; 60 NocoDB release bodies scanned by keyword are not counted), 284 entries in the lists that can be counted (Dolibarr 165, Frappe 71, Vikunja 27, NetBox 15, ERPNext 6), 9 applications examined, 7 yielding a candidate. The search stopped at twelve candidates because that is the bound, not because the sources were exhausted.

## What was not read

- Any directory named scorer, sealed, blind-holdout, blind-holdout-v2, blind-holdout-v3, and any file whose name contains answer, sealed or oracle (including oracle.json in the lane directory).
- The blind-holdout result notes and receipts, the suffix-* files, and the gate runners, which were not needed.
- Changelogs of Redmine, Taiga, Plane, Monica, InvoiceNinja, Leantime and Baserow. They were on the suggested list and were not reached; nothing is claimed about them.
- OpenProject release notes between those listed, and ERPNext release notes for individual version-15 minors other than through the source bisect.

## Not confirmed

- Nothing was run. Every disposition is a prediction from reading.
- L1: that the PATCH answers 200 rather than an error when it carries only the dropped link; and the state of work_package_multiple_versions on the instance that will be tested.
- L2, L3: that no NetBox layer outside the serializers rejects undeclared keys.
- N1: that the timesheet fixture is accepted as written and the acting roles suffice on both tags.
- N2: how the official image enables modules and API keys.
- N3: B's rescheduled dates (derived from the stored lag).
- N4: that the API create path leaves the new column default in place and nothing switches the mode when a predecessor is added.
- N5: default board columns on a fresh 0.23.0 project and their in-place migration.
- N6: that the ERPNext bring-up and a workable role set exist for v15.126.0 and v16.0.0.
- N7: everything beyond the release note.
- L4: what the unlicensed Community Edition does with approvals_before_merge.
- Unpacked disk sizes and all bring-up times marked as estimates.

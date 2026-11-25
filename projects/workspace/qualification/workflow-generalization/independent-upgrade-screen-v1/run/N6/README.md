# N6: ERPNext v15.126.0 to v16.0.0, default list order changes

**Status: draft, never run.** The owner paused the screen before this case started. No site of either release
was created for it and nothing here has been executed; `case_meta.py` holds intended conditions, not observed
ones. There is no `run.sh` yet.

Open before any run:

- whether the frozen `../../../bringup/erpnext-up.sh v15.126.0 v16.0.0` and its seeder work on these two
  releases. The v16.0.0 image was only inspected, not started as a site: `bench new-site` still accepts the
  flags the frozen script passes, and the setup-complete flag the frozen seeder reads has moved from System
  Settings to the installed-application records, so the seeder may need a copy under this directory;
- the sealed list says "Submit that quotation" without naming the request. `run_case.py` fixes it as
  `PUT /api/resource/Quotation/{name}` with `{"docstatus": 1}`, identical on both releases. That choice was
  made before any run and has not been tried.

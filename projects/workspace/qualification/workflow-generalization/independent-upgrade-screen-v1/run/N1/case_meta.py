"""N1: what the operator of the run records beside the raw evidence."""

CASE = "N1"

FLAGS = []

CONDITIONS = {
    "install": "fresh site of each release on an empty database (bench new-site --install-app erpnext); "
               "no in-place upgrade was run",
    "bring_up": "bringup/erpnext-up.sh v15.53.0 v15.54.0, unchanged, once per repeat; bringup/erpnext-down.sh "
                "after each repeat",
    "host": "Docker Desktop on Apple silicon running the linux/amd64 images under emulation; MariaDB 10.6 and "
            "Redis 6.2 in their own containers",
    "time_zone": "site time zone UTC (set by the frozen seeder's setup wizard call)",
    "acting_account": "seeded stage2_author@isolated.local with its own API key; roles Purchase User, Purchase "
                      "Manager, Accounts User from the seeder, plus Projects User added in set-up",
    "set_up_means": "the application's REST API in a session of Administrator",
    "settings_that_matter": "Projects Settings 'Fetch Timesheet in Sales Invoice' is left at the release's "
                            "default; the stored value is read per repeat (the field does not exist on v15.53.0)",
    "gates_B_and_C": "same v15.54.0 site within a repeat, separate customer, project and timesheet",
    "stored_value_read": "MariaDB in the database container (docker exec ... mariadb), after the response",
}

DEVIATIONS = []

PREDICTION_NOTES = (
    "The request, the stored rows and the response are as the sealed prediction says: every call answers 200, "
    "the invoice is submitted with no Sales Invoice Timesheet row and total_billing_hours 0, the timesheet stays "
    "at per_billed 0 with status Submitted and its detail row has no sales_invoice. Projects Settings "
    "fetch_timesheet_in_sales_invoice was 0 on the fresh v15.54.0 site in every repeat and absent on v15.53.0."
)

DIGEST_NOTES = "All four images are the sealed linux/amd64 digests."

NOTES = [
    "Sealed names: \"customer\": \"CUST-A\" and \"project\": \"PROJ-A\" are sent literally. A project's document "
    "name comes from a naming series (PROJ-0001), so set-up renames each project with frappe.client.rename_doc "
    "as Administrator. The sealed list leaves company and item_code open; they are Stage2 Qual Corp and SVC-A.",
    "Repeat 1 ran by hand on a pair brought up with the same frozen command, as the runner's first execution "
    "ever; repeats 2 and 3 ran through run.sh. Between them only the recording changed: response excerpts now "
    "have credential fields redacted, and the API key that the application echoed in repeat 1's set-up responses "
    "was redacted in the stored evidence.",
    "The query for installed application versions returned no row on these releases; the image digests pin the "
    "versions.",
]

VOIDED_ATTEMPTS = [
    {"what": "first bring-up of the pair, before any observation",
     "started_utc": "2026-11-25T14:20:29Z",
     "why_void": "the Docker engine answered 500 to the bring-up's own docker exec while the second site was "
                 "being created (a pull running beside it ended with 'unexpected EOF' at the same moment); the "
                 "frozen script exited 1 before seeding. No request was sent to either site. Everything was "
                 "removed and the pair was brought up again from nothing."},
]

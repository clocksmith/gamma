"""N6: what the operator of the run records beside the raw evidence."""

CASE = "N6"

FLAGS = []

CONDITIONS = {
    "install": "fresh site of each release on an empty database (bench new-site --install-app erpnext); "
               "no in-place upgrade was run, so no saved per-user list setting exists on either site",
    "bring_up": "to be recorded",
    "host": "Docker Desktop on Apple silicon; MariaDB 10.6 and Redis 6.2 in their own containers",
    "time_zone": "site time zone UTC (set by the seeder's setup wizard call)",
    "acting_account": "seeded stage2_author@isolated.local with its own API key; roles from the seeder plus "
                      "Sales User and Sales Manager added in set-up",
    "set_up_means": "the application's REST API in a session of Administrator: customer CUST-Q; per gate two "
                    "draft quotations Q1 then Q2, two seconds apart, and two seconds later an edit of Q1",
    "submit_request": "the sealed list says 'Submit that quotation' without naming the request; fixed before "
                      "any run as PUT /api/resource/Quotation/{name} with {\"docstatus\": 1}, identical on both "
                      "releases",
    "gates_B_and_C": "same v16.0.0 site within a repeat; before gate C's quotations are made, the draft left "
                     "by gate B is deleted by Administrator so that gate C reads only its own drafts",
    "stored_value_read": "MariaDB in the database container (docker exec ... mariadb): docstatus of every "
                         "quotation, after the response",
}

DEVIATIONS = []

PREDICTION_NOTES = ""

DIGEST_NOTES = ""

VOIDED_ATTEMPTS = []

"""N3: what the operator of the run records beside the raw evidence."""

CASE = "N3"

FLAGS = ["deviated-from-sealed-steps"]

CONDITIONS = {
    "install": "fresh install of each release on an empty database (the frozen bring-up migrates a new database "
               "per release); no in-place upgrade was run",
    "bring_up": "bringup/openproject-up.sh 13.4.0-slim 14.0.0-slim, unchanged, once per repeat; "
                "bringup/openproject-down.sh after each repeat",
    "host": "Docker Desktop on Apple silicon (linux/arm64 images), PostgreSQL 15 in its own container",
    "time_zone": "containers run in UTC; all fixture dates are plain dates",
    "acting_account": "seeded project member stage2_author (role Stage2AuthorRole), own API token",
    "permission_set_up": "manage_work_package_relations added to Stage2AuthorRole on both releases with "
                         "Role#add_permission! in rails runner, the role model the frozen seeder itself uses",
    "settings_that_matter": "working days Monday to Friday and no non-working days (read from the database in "
                            "every repeat); work packages are created through the API by the acting account "
                            "and are automatically scheduled (schedule_manually false on both releases)",
    "gates_on_one_instance": "within a repeat the 14.0.0 instance serves gates B and C, and each instance "
                             "serves the sealed and the corrected variant, always on a new pair of work packages",
    "stored_value_read": "PostgreSQL in the database container (docker exec ... psql): the relations row and "
                         "the work_packages rows of A and B, read after the response",
}

DEVIATIONS = [
    {
        "what": "The sealed request does not work as written on the from-version (nor on the to-version).",
        "evidence": "POST /api/v3/work_packages/{B}/relations with {\"type\": \"follows\", \"delay\": 3, "
                    "\"_links\": {\"to\": {\"href\": \"/api/v3/work_packages/{A}\"}}} answered HTTP 500 "
                    "'An internal error has occurred. undefined method `id' for nil:NilClass' and stored no "
                    "relation, on 13.4.0 and on 14.0.0, in all three repeats (gates recorded under gate_A, "
                    "gate_B, gate_C of each repeat). The same request with lag answered 500 as well. On a "
                    "development instance before the counted repeats the error was traced with the service "
                    "called directly: it is raised in relatable_ensure_single_relation "
                    "(app/models/work_packages/scopes/relatable.rb:421) under "
                    "Relations::BaseContract#validate_nodes_relatable, because the relation has no `from` "
                    "work package. The endpoint of these releases does not take `from` from the path.",
        "smallest_correction": "\"from\": {\"href\": \"/api/v3/work_packages/{B}\"} added to _links. Method, "
                               "path, type, the delay or lag property, the `to` link and the success criterion "
                               "(HTTP 201) are unchanged. The corrected requests are recorded under `corrected` "
                               "in each repeat, on separate work packages, and decide the disposition above.",
        "for_the_judge": "By the README's rule the steps exactly as sealed are a setup-block (the old workflow "
                         "never worked). The disposition reported for the case is that of the corrected steps.",
    },
]

PREDICTION_NOTES = (
    "Scored against the corrected steps. The sealed detail 'The POST answers 201' does not hold for the request "
    "as sealed (500 on both releases). With the correction the POST answers 201 on 14.0.0, the relation is stored "
    "with lag NULL (the sealed list predicted 0; the generated column `delay` is NULL too) and B starts on "
    "2026-03-03, as predicted. The response body itself shows \"lag\": null."
)

DIGEST_NOTES = (
    "Both OpenProject images are the sealed arm64 digests. postgres:15 is not: the bring-up used the copy of "
    "postgres:15 that was already on the machine (built 2025-12-08), which belongs to other work there and was "
    "not pulled again; the sealed list records the registry's tag as pushed on 2026-11-24."
)

VOIDED_ATTEMPTS = []

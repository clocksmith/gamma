"""N4: what the operator of the run records beside the raw evidence."""

CASE = "N4"

FLAGS = []

CONDITIONS = {
    "install": "fresh install of each release on an empty database (the frozen bring-up migrates a new database "
               "per release); no in-place upgrade was run",
    "bring_up": "bringup/openproject-up.sh 15.3.0-slim 15.4.0-slim, unchanged, once per repeat; "
                "bringup/openproject-down.sh after each repeat",
    "host": "Docker Desktop on Apple silicon (linux/arm64 images), PostgreSQL 15 in its own container",
    "time_zone": "containers run in UTC; all fixture dates are plain dates",
    "acting_account": "seeded project member stage2_author (role Stage2AuthorRole), own API token",
    "permission_set_up": "manage_work_package_relations added to Stage2AuthorRole on both releases with "
                         "Role#add_permission! in rails runner, the role model the frozen seeder itself uses",
    "settings_that_matter": "working days Monday to Friday and no non-working days; the column default of "
                            "work_packages.schedule_manually (read from the database in every repeat, on both "
                            "releases); nothing was switched by the run",
    "gates_on_one_instance": "within a repeat the 15.4.0 instance serves gates B and C, always on a new pair of "
                             "work packages",
    "stored_value_read": "PostgreSQL in the database container (docker exec ... psql): the work_packages rows "
                         "of A and B and the relations row, read after the responses",
}

DEVIATIONS = []

PREDICTION_NOTES = ""

DIGEST_NOTES = ""

VOIDED_ATTEMPTS = []

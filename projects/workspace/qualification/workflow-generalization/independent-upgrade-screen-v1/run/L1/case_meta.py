"""L1: what the operator of the run records beside the raw evidence."""

CASE = "L1"

FLAGS = []

CONDITIONS = {
    "install": "fresh install of each release on an empty database (the bring-up migrates a new database per "
               "release); no in-place upgrade was run. The sealed prediction is conditional on this: on a fresh "
               "17.8.0 the setting work_package_multiple_versions defaults to on; on a database seeded under "
               "17.7.0 and upgraded in place it is predicted to stay off. That second condition was not run.",
    "bring_up": "screening/openproject-up.sh 17.7.0-slim 17.8.0-slim (byte-identical copy of the frozen "
                "bring-up, mounting the screening seeder, as the sealed list names for this pair), once per "
                "repeat; bringup/openproject-down.sh after each repeat",
    "host": "Docker Desktop on Apple silicon (linux/arm64 images), PostgreSQL 15 in its own container",
    "time_zone": "containers run in UTC; the case has no dates",
    "acting_account": "seeded project member stage2_author (role Stage2AuthorRole), own API token",
    "set_up": "in rails runner on both releases: assign_versions added to Stage2AuthorRole with "
              "Role#add_permission!, version 'Sprint 3' created in stage2-qual-proj, and the setting read and "
              "printed before the first request; the work package W is created by the acting account through "
              "the API",
    "settings_that_matter": "work_package_multiple_versions, read per repeat on both releases before the first "
                            "probe (see setup.sides in each repeat); nothing was switched by the run",
    "gates_B_and_C": "same 17.8.0 instance within a repeat, separate work packages, the same version",
    "stored_value_read": "PostgreSQL in the database container (docker exec ... psql): work_packages.version_id "
                         "and the rows of work_package_versions for W, after the response; a GET of W with the "
                         "other seeded account (stage2_approver) as a second witness",
}

DEVIATIONS = []

PREDICTION_NOTES = (
    "One repeat only; not scored. In that repeat, as predicted for a fresh install: the setting "
    "work_package_multiple_versions read false on the fresh 17.7.0 and true on the fresh 17.8.0 before the "
    "first request. On 17.8.0 the PATCH with "
    "_links.version answered 200 and changed nothing: no work_package_versions row, work_packages.version_id "
    "NULL, lock_version and journal count unchanged; the second account's GET showed no version link and "
    "targetVersions []. The other half of the sealed condition was not run: an in-place upgrade of a database "
    "seeded under 17.7.0, where the setting is predicted to stay off and the old steps to keep working."
)

DIGEST_NOTES = (
    "Both OpenProject images are the sealed arm64 digests. postgres:15 is not: the bring-up used the copy of "
    "postgres:15 that was already on the machine (built 2025-12-08), which belongs to other work there and was "
    "not pulled again; the sealed list records the registry's tag as pushed on 2026-11-24."
)

NOTES = [
    "On 17.7.0 the old PATCH wrote work_packages.version_id and also a work_package_versions row of kind "
    "'target'; the table already exists in that release.",
    "On 17.8.0 the correct path writes the work_package_versions row and leaves work_packages.version_id NULL "
    "and lock_version unchanged; the sealed right value names only the row.",
    "Repeat 1 ran by hand on a pair brought up with the same command, as the runner's first execution ever and "
    "without any change afterwards. It is the only repeat observed: the owner paused the work while repeat 2 "
    "was being brought up through run.sh. Repeats 2 and 3 are still to be run.",
]

VOIDED_ATTEMPTS = [
    {"what": "repeat 2, attempt 1",
     "started_utc": "2026-11-25T15:28:51Z",
     "why_void": "abandoned during bring-up when the owner paused the work, about half a minute in: the 17.8.0 "
                 "database was still being migrated and no request had been sent to either release. The "
                 "containers, the network and their anonymous volumes were removed."},
]

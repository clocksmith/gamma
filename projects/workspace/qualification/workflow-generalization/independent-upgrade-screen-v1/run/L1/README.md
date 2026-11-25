# L1: OpenProject 17.7.0 to 17.8.0, `version` replaced by `targetVersions`

**Status: incomplete, paused by owner.** One repeat was observed (`../../results/L1.partial.json`); repeats 2
and 3 are still to be run with `REPEATS="2 3"`, after which `assemble.py` writes `../../results/L1.json`.

One command runs the whole case (three repeats, each on a freshly brought-up pair, then the result file):

```text
SCREEN_OUT_DIR=<scratch directory> SCREEN_HOLD_FILE=<hold marker file> ./run.sh
```

| File | What it does |
| --- | --- |
| `run.sh` | Per repeat: waits while the hold marker exists, runs `../../../screening/openproject-up.sh 17.7.0-slim 17.8.0-slim`, runs `run_case.py`, runs the frozen `../../../bringup/openproject-down.sh`, removes the anonymous volumes its own containers had mounted. A repeat that overlapped a hold is set aside as void and run again on a fresh pair. Ends with `assemble.py`. |
| `run_case.py` | Set-up, gates A, B and C, and the database reads, for one repeat. Writes `repeat-<n>.json` to `SCREEN_OUT_DIR`. |
| `assemble.py` | Applies the disposition table of `../../README.md` to the three repeats and writes `../../results/L1.json`. |
| `case_meta.py` | The case's conditions, deviations and notes, as recorded by the runner's operator. |
| `screenlib.py` | Request, command and hold helpers (Python standard library only). |

The bring-up is the screening copy, not the frozen one: the frozen seeder cannot create its projects from
OpenProject 16.4.0 on. `../../../screening/openproject-up.sh` is byte-identical to the frozen script and mounts
the screening seeder that lies beside it. Neither is edited.

## Set-up

In `rails runner`, on both releases: `assign_versions` is added to the seeded role `Stage2AuthorRole`, the
version `Sprint 3` is created in `stage2-qual-proj`, and the setting `work_package_multiple_versions` is read
and printed before any request. For every gate the acting account, the seeded project member `stage2_author`,
creates a work package W through `POST /api/v3/projects/{P}/work_packages`.

## What each gate sends, as `stage2_author` with its own API token

- Gate A, 17.7.0: `GET /api/v3/work_packages/{W}`, then `PATCH /api/v3/work_packages/{W}` with
  `{"lockVersion": n, "_links": {"version": {"href": "/api/v3/versions/{V}"}}}`.
- Gate B, 17.8.0: the identical two requests.
- Gate C, 17.8.0, a second work package: the same with
  `"_links": {"targetVersions": [{"href": "/api/v3/versions/{V}"}]}`.

Success is HTTP 200 on the PATCH. The stored value is read from PostgreSQL in the database container:
`work_packages.version_id` of W and the rows of `work_package_versions` for W. Right value, from the sealed
list: on 17.7.0 `version_id` = V; on 17.8.0 exactly one `work_package_versions` row for W with version V and
kind `target`. A `GET` of W with the other seeded account is kept as a second witness.

No secret is written to the evidence: credentials are recorded as `<redacted>`.

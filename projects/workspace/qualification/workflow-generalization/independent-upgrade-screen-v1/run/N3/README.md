# N3: OpenProject 13.4.0 to 14.0.0, relation `delay` renamed `lag`

One command runs the whole case (three repeats, each on a freshly brought-up pair, then the result file):

```text
SCREEN_OUT_DIR=<scratch directory> SCREEN_HOLD_FILE=<hold marker file> ./run.sh
```

| File | What it does |
| --- | --- |
| `run.sh` | Per repeat: waits while the hold marker exists, runs the frozen `../../../bringup/openproject-up.sh 13.4.0-slim 14.0.0-slim`, runs `run_case.py`, runs the frozen `openproject-down.sh`, removes the anonymous volumes its own containers had mounted. A repeat that overlapped a hold is set aside as void and run again on a fresh pair. Ends with `assemble.py`. |
| `run_case.py` | Set-up, gates A, B and C, and the database reads, for one repeat. Writes `repeat-<n>.json` to `SCREEN_OUT_DIR`. |
| `assemble.py` | Applies the disposition table of `../../README.md` to the three repeats and writes `../../results/N3.json`. |
| `case_meta.py` | The case's conditions, deviations and the image-digest comparison, as recorded by the runner's operator. |
| `screenlib.py` | Request, command and hold helpers (Python standard library only). |

## Deviation from the sealed steps

The sealed request names only `_links.to`. Sent exactly so, it answers HTTP 500 on 13.4.0 and on 14.0.0 and
stores nothing: the endpoint of these releases does not take the relation's `from` end from the path. Each
repeat therefore records two variants, on separate work packages:

- `gate_A`, `gate_B`, `gate_C`: the request exactly as sealed (no `_links.from`);
- `corrected.gate_A`, `corrected.gate_B`, `corrected.gate_C`: the same request with
  `"from": {"href": "/api/v3/work_packages/{B}"}` added to `_links`, nothing else changed.

The result file reports the disposition of the corrected steps under the flag `deviated-from-sealed-steps`, and
the verdict of the steps exactly as sealed beside it.

## What each gate sends

Set-up, both releases: `manage_work_package_relations` is added to the seeded role `Stage2AuthorRole` with
`Role#add_permission!` in `rails runner` (the role model the frozen seeder itself uses). The acting account is
the seeded project member `stage2_author`, with its own API token. For every gate that account creates two work
packages through `POST /api/v3/projects/{P}/work_packages`: A and B, both starting and finishing on Monday
2026-03-02.

- Gate A, 13.4.0: `POST /api/v3/work_packages/{B}/relations` with
  `{"type": "follows", "delay": 3, "_links": {"to": {"href": "/api/v3/work_packages/{A}"}}}`.
- Gate B, 14.0.0: the identical request.
- Gate C, 14.0.0, a second pair of work packages: the same request with `"lag": 3` in place of `delay`.

Success is HTTP 201. The stored value is read from PostgreSQL in the database container
(`docker exec gammatron-op-pg15 psql ...`): the `relations` row (`delay` on 13.4.0, `lag` on 14.0.0) and
`work_packages.start_date` of B. Right value, from the sealed list: gap 3 and B starting on 2026-03-06.

No secret is written to the evidence: credentials are recorded as `<redacted>`.

# Status: paused by the owner on 2026-11-25, about 15:29 UTC

The screen stopped part-way through its sealed list. Nothing is running. Nothing here has been rerun by the
screener or checked by anyone outside; every line below is one run by one operator.

The protocol (`README.md`) and the sealed list (`screen-list.json`) are unchanged.

## Where each case stands

| Case | Upgrade | State | Disposition | Sealed prediction |
| --- | --- | --- | --- | --- |
| `N1` | ERPNext v15.53.0 to v15.54.0 | complete, 3 of 3 on every gate | `silent-wrong-write` | right, including the stored values |
| `N2` | Dolibarr 18.0.9 to 19.0.2 | complete, 3 of 3 on every gate | `silent-wrong-write` | right |
| `N5` | Vikunja 0.23.0 to 0.24.0 | complete, 3 of 3 on every gate | `silent-wrong-write` | right |
| `L2` | NetBox v4.0.11 to v4.1.0 | complete, 3 of 3 on every gate | `silent-wrong-write` | right |
| `L3` | NetBox v4.1.11 to v4.2.0 | complete, 3 of 3 on every gate | `silent-wrong-write` | right |
| `N3` | OpenProject 13.4.0 to 14.0.0 | complete, 3 of 3 on every gate, **with a flagged correction** | `silent-wrong-write` for the corrected steps; `setup-block` for the steps exactly as sealed | right on disposition and date; wrong on two details |
| `L1` | OpenProject 17.7.0 to 17.8.0 | 1 repeat of 3 | none yet | not scored |
| `N7` | NocoDB 0.107.5 to 0.108.0 | gate A only, 3 of 3 | none yet | not scored |
| `N4` | OpenProject 15.3.0 to 15.4.0 | not started; draft scripts only | none | not scored |
| `N6` | ERPNext v15.126.0 to v16.0.0 | not started; draft scripts only | none | not scored |
| `L5` | GitLab CE 15.11.13 to 16.0.0 | not started | none | not scored |
| `L4` | GitLab EE 15.11.13 to 16.0.0 | excluded before any run: needs a paid licence | `not-run` | not scored |

**Count so far: 6 of 12 screened to completion. 5 qualify with no deviation; 1 qualifies only with a flagged
correction.** Six cases are unfinished or not run, so this is not the screen's final count.

## What a reader should know before quoting this

- **`N3` deviated from the sealed steps.** The sealed request left out the relation's `from` link and answered
  HTTP 500 on both releases, which by the protocol is a set-up block. With that one link added and nothing else
  changed, the old release stored the right value and the new release answered 201 and stored the wrong one. Both
  variants are recorded in every repeat. Whether that counts is a judgement, not a measurement.
- **Selection.** The list starts from documented changes and picks the workflow each one touches. These results
  say such failures exist on real software. They say nothing about how often an arbitrary workflow meets one.
  Earlier screens that held one workflow fixed across 38 real version pairs found none.
- **Two of the lane's own five catalogue entries are among the completed cases (`L2`, `L3`).** On the real software
  the old request is accepted and the wrong value is stored. The lane's stand-in servers for the same upgrades
  answer the old request with an error.
- **Often visible in the response.** In several cases the response body itself shows the wrong or missing value;
  a client that checks only the status code misses it. No guard was tested here.
- **Paid Stage A stays parked.** A qualifying case is an input to a later comparison of guards, owned by a party
  other than the builder. Nothing in this directory un-parks it.

## To resume

1. Start Docker, check at least 25 GiB free, take the port leases.
2. `run/L1`: `REPEATS="2 3" ./run.sh` finishes it. `run/N7`: gates B and C still need a 0.108.0 instance; the one
   attempt exited six seconds after start with a TypeError and was not diagnosed.
3. `run/N4`, `run/N6`, `run/L5`: drafts that have never been executed. Read their README files first.
4. The screener reruns one repeat of at least one qualifying case by hand before any of this is called confirmed.
5. Images pulled for the screen are still in the local Docker store. Raw per-repeat evidence is kept outside the
   repository.

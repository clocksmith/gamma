# Amendment 1, 2026-10-23: exposure, replay, runtime caps and the pre-freeze receipt (before launch)

Nothing has launched. These changes come from codex's review of `942f8cc6e` (gamma-team LOG, 21:49Z).

1. **Fit-only exposure before the seal.** The searched arms now read only the seed dictionary and item 13's
   `fit-sources.json`, pinned by private SHA-256 in the contract. `sources.json`, which holds the validation
   sources, is read only after the arm's dictionary and fit seal are written. The arm then checks that its fit
   portion equals `fit-sources.json`. Before this change, `load_seed()` parsed all 400 sources before the
   search, although no validation value was used. The fit seal's `validation_loaded: false` is now true of
   the process, not just of the scoring.
2. **Independent replay in evidence.py.** For each arm, evidence.py re-reads the sealed `dictionary.json`. It
   checks the dictionary's hash against both the fit seal and the arm's reported hash, checks that it has at most
   256 entries, and re-measures all 400 sources through the canonical codec. It asserts that every per-program
   row, the dictionary bytes and the illegal-entry list equal the arm's own report. All decision rules then use
   the replayed rows. A missing arm or a nonzero exit code is recorded under `failed_arms` and is never dropped.
   An illegal entry fails readiness rather than crashing the replay. The decoder dependency source bytes and
   the offline encoder inventory are reported separately, following the item 24 and 27 standard.
3. **Hard caps and runtime pin.** Each arm process runs under `timeout 7200` and a 10 GiB address-space limit
   (RLIMIT_AS). For scale, item 22's arms use about 3.0 GB resident and 4.5 GB virtual. The search policy is
   unchanged: a 5,400 s LNS budget and 300 s per repair. The cap also covers pool setup, the last repair and the
   validation measurement. An arm killed by either cap is a retained failure. The contract now pins the
   interpreter by its real path and SHA-256 (`/usr/bin/python3.14`, 3.14.4, behind the `.venv_rocm` launcher)
   and scipy 1.18.1. `contract()` verifies all three before any work.

## Pre-freeze corpus exposure, retained

Two runs touched the corpus between writing FREEZE.md and the freeze commit. FREEZE.md declared them, but they
were not synthetic. They are kept, not erased:

- **Fit-only smoke**: `succ.py --smoke 120`, all three arms, cores 11–13, ending 21:46:19Z (receipt file times; started about two minutes earlier). Each arm made exactly
  one repair, a 120 s HiGHS time-limited move. The results:
  - unweighted: feasible, not an improvement;
  - nonregress: no feasible point;
  - relative: feasible, rescored at 29,453 fit selections, not an improvement.

  No move was accepted. Every arm's final dictionary equals the seed's list, with fit at 24,750. The old
  `load_seed()` **loaded** `sources.json`, including all 100 validation sources, into the smoke processes. No
  validation value was used by the optimizer or scored, and smoke mode returns before measurement. The receipt is in private storage at `breadth13/smoke-prefreeze/`:

  | File | SHA-256 |
  | --- | --- |
  | `results.json` | `ae8052f3d418e9abfe3b4c8dc782f91ee4f35842bc6449805ba3a9d73de90c1e` |
  | each `dictionary.json` | `de15a9a5d392bd3d4979ec6f0e77a7287adc9e38e4c4269dd8d78fb3ad700300` |
  | unweighted `moves.jsonl` | `58073740a98bddfb83197c5fcc4cfd2a24f7ec6b968ebcdc2613d82fe3968b8b` |
  | nonregress `moves.jsonl` | `b07102bf6ef714e7537c51c1df4db7e84f2778feb661260eac0f20f08c074643` |
  | relative `moves.jsonl` | `2f04a3a3f4a00e8d47470b429b3703e1d4e21cc02d6434bc6d9000ad4fd7878c` |

- **Evidence stand-in**: evidence.py run end to end on a stand-in arm equal to the unchanged seed, which
  re-measures item 13's existing validation results. The stand-in reproduces item 13 (8,504 actions; 75/21/4
  against R). Seed against item 24 is 14/53/33. The receipt is `breadth13/standin-prefreeze/results.json`,
  `2f0c9a7965f7de495ce2b49368359c261119d087cb08791be9f5c1d5b2281513`.

Neither run changed any parameter, prediction or rule.

After this amendment's code changes there was one more stand-in check, again only re-measuring the unchanged
seed and doing no search. Two stand-in arms carried sealed seed dictionaries, and a third was missing with exit 1.
The replay asserts passed, and the missing arm was recorded under `failed_arms`. The receipt is
`breadth13/standin2-prefreeze/results.json`, `da884671c01b132970fa18f496e9b034566c02b7b0a2a01da112170e14cd5e31`.
The loaders, `contract()` and the caps were checked without search: RLIMIT_AS reads 10 GiB in the child, and
`timeout` returns 124. There is no further corpus run before launch.

No objective, arm, budget, prediction or decision rule changes. This file is added to the contract.

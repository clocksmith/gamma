# Cross-review and execution receipt

Freeze `2523d591c` was pushed to origin/main before review and execution.
Claude approved at 2026-10-23T17:29Z through the append-only team LOG.md.

## Review reply

A review (cost-decomposition-v1 @ 2523d591c): approve, launch when ready
Checked FREEZE.md, analyze.py, lexical.cjs and the contract.
- Held-out safety: contract lists exactly 400 sources = minify-control dev_fit 300 + dev_val 100, all under
  style150/ or scale500/; load_sources reads only those paths; no pools() call. Good.
- Capacity proof is correct: an entry private to one of the 400 benefits only that program, so <=K programs can
  beat b_p; lowering the K largest b_p to 2 leaves the remaining multiset elementwise minimal, so the bound holds
  for total and every order statistic simultaneously. shared_lengths' nearest-different-owner-neighbour LCP is
  correct for the sorted suffix array; fit_oracle's bisect neighbours are correct.
- Labelling: the capacity rows use all 400 for sharing, so their dev-val slices are retrospective, not
  validation; please label any dev-val-only view of them that way (FREEZE already says it for the 400).
- Optional tighter, codec-specific row (label it so): our codec keeps every used character as a single entry,
  so only K minus (distinct characters in the 400) slots can be private; same proof. Not required.
- Attribution tie rule: shortest_encode ties to the smaller first ID, the canonical segment() ties the same way,
  so A1 totals and the per-selection split should match. Predictions A1-A5 are fine as written.
No objections to launch.


## Execution

Launched after reading the approval and BOARD at 2026-10-23T17:29Z.
Host load was 2.25 / 2.60 / 2.79. One worker, system Python 3.14.4, Node v22.22.1.
The launcher enforced `timeout --signal=TERM 1200 prlimit --as=2147483648`.
Exit status 0; all 800 packets independently decoded and both dev-val baselines reproduced.
No review timeout or design amendment. The optional tighter row suggested in review was not added.

Private run: `$W/cost-decomposition/run-v1`; private log SHA-256 `738a3673385963be8b36efd088454455423524f63b603b98aa1e2fc62e3a8dc7`.
Source bodies were neither changed nor freshly executed; prior hash-bound qualification is reused.

The final held-out sources were not opened. The shared-substring oracle intentionally uses
all 400 development sources; it is retrospective, not an untouched-validation score.

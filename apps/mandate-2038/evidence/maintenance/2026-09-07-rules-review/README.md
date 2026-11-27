# Rules-review corrections, 2026-09-07

Component: Mandate 2038 rules, Government Headline rewards, physical Trust
records, and player aids.

Intent: preserved overall. The provisional Government interpretation deliberately
replaces the engine's first-matching-tile choice with one reward per institution
controlling at least one Government district. Controlling both does not double
the reward. Compute Borders Harden retains a separate Chip reward. This follows
the proposed default while the user's recipient preference remains unanswered.

## Changes

- Both Government Headlines specify recipients and multiplicity. Existing
  district control determines eligibility, including contested districts.
- Trust has three permanent-for-the-game award boxes beside its current slider.
  Starting thresholds are premarked; Audit losses and Era resets never clear
  them. Gallery faction cards derive their marks from canonical starting Trust
  and scoring thresholds, including Orisonix's already-scored four threshold.
- Contract hosts explicitly permit multiple Joint Ventures per Facility,
  repeated contracts between a pair, and coexistence with one Mega-Cluster.
  Each venture requires another action, consent, and available pair; each
  active contract pays separately. These permissions retain existing execution.
- Teaching proceeds through setup, resources, ReAct, the six actions, Era
  resolution, later unlocks, and final scoring before references. Build contains
  Facility, ordinary Generator, Mega-Cluster, and Fusion construction details.
- Player aids include faction Production income first, the compulsory Runway
  then Trust loss order with zero fallback, both Open conditions beside the
  ending matrix, and correct rounding. Historical exclusions leave teaching.

## Acceptance evidence

`baseline.log` runs the new Government regression against an isolated copy of
the original engine: the second Government controller incorrectly receives no
Runway. The repaired engine passes all six regressions in `focused.log`.

`snapshot-contracts.log` records **68 passing document and game-contract tests**.
`snapshot-check.log` records a passing `npm run check`. `stable.log` records
seven passing checks, including the deterministic simulation test that failed
with changing source identity in the working checkout. `browser-final.json`
and `trust-final.png` record Chrome inspection of all six faction cards and
eighteen correctly premarked boxes.

The full working-tree run in `tests.log` records **280 passes and 12 failures**.
It predates corrected assertions and overlaps another writer's lore-authoring
changes. Failures include stale source assumptions, changing execution identity,
and frozen release mismatch. `owning-tests.log` records 161 passes and one
source-identity failure; that case passes in the stable copy. These adverse
runs remain evidence, not clean full-suite acceptance. Intermediate contract
failures are retained as well.

`tested-source.tar.gz` preserves the final snapshot's authored files, tests,
runtime, and generated documents. `tested-source-files.json` lists their hashes.
`receipt.json` binds logs and archive. Historical version directories and the
existing evidence tree remain in the repository; they are not duplicated in
the source archive. To rerun all snapshot checks, extract into a fresh directory
and supply those unchanged directories from the recorded source base. Run
`npm run build:all`, `npm run check`, and the test commands named by the logs.

Boundary effects: card wording and engine recipients, physical state encoding,
gallery cards, teaching order, generated references, and regression assertions.
Concurrent lore work remains intact. No new resource, phase, action, simulation
balance promotion, human playtest, immutable release, or publication is claimed.

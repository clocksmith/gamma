# Item 47 pending execution freeze: capped canonical fraction exchange

Pending root review, pushed freeze and Claude cross-review. No private source,
dictionary, q, case or experiment input was opened in preparing this implementation.
The binder writes an inactive pending contract. Activation must regenerate the
entire identical payload and verify every public code/runtime pin before changing
only active=false to active=true. Root owns activation, commit and launch.

## Population, representation and baseline

Use exactly item 40's R/naming 300-fit sources, bounded pools and 249-entry seeds,
with the original source-hash qualification receipts. Rebuild and compare the
parent full-substring pool/seed binding, bans and candidate identities; do not
select a parent witness after inspection. Only the seed dictionary is loaded as
a witness; parent warm/cold dictionary files are unnecessary and unbound here.
Parent q is read solely to reconstruct the unchanged item 40 pool, never optimized
or used as a canonical path score. No validation, fresh cases, source alternatives,
source execution, protected/final-heldout inputs or training.

The public item 44 primary and canonical-shadow records, recorded in 07d99f2f2,
bind each seed's sorted-dictionary canonical packet, C/N and exact per-program cap.
The cap vector is (program ID, original source hash, canonical seed N). R seed
N=26,108 and naming N=24,750. These are sorted-subset policy baselines, not
historical original-order canonical ties. A mismatch fails before search.

Every entry, including every singleton, is paid. Capacity is <=256, no free
character fallback. Characters can be removed only when the full candidate remains
covered and satisfies every cap. Global complete-source/solve-body bans remain.
One-owner and near-whole substrings are permitted in this relaxation and are
reported, not asserted to meet semantic-reuse requirements. No M1 candidate,
current-best replacement, 400/500 exclusion or default promotion is authorized.

## Exact scoring and frozen search

Assign fixed IDs in sorted pool order; active dictionaries are sorted subsets.
Canonical encoding minimizes (N, complete ID sequence), with no C tie break and
no minimum-F path. Relative ID order remains stable after additions/removals;
transmitted packets use dense subset IDs. N counts selections excluding Finish;
actions add one per program. Every candidate must satisfy N_p<=seed_N_p for all
300 programs, which prevents every seed-relative action regression and quantile
regression. Caps do not tighten after acceptance: adjacent-incumbent increases
within the original caps are allowed and disclosed.

Strict admission is lexicographic (exact aggregate C/N, aggregate N, full package).
Compare ratios with arbitrary-precision integers, never rounded floats. Report
C, N, fraction and every per-program change, including equal-ratio plateaus.
Fixed decoder source bytes are included in the package objective. Package accounting
charges the shared dictionary once, eight-bit selections, 41 packet framing bytes
per program and zero padding; offline tools and source bytes are separate.

Up to seven free-slot addition sweeps precede at most twelve exchange epochs;
an earlier complete sweep with no improvement ends the free-slot phase. Each epoch
uses one immutable incumbent: all absent additions, all present removals, then
four best addition ranks crossed with every present removal. Rank by exact
(ratio,N,package), then fixed added pool ID. Temporary capacity 257 is ranking-only,
never retained or serialized. Standalone coverage/cap failure does not filter a
swap: direct joint evaluation may repair it. The top-four shortlist is a heuristic,
not a bound on omitted swaps. No local/global optimum follows from this procedure.

Freeze each sweep's ordered opportunity hash/count and shortlist before probing.
Record each probe start time after its budget guard; no new probe starts at or
after the 600-second limit. Count every attempted addition/rank/removal/swap/full rescore, including coverage
failures, cap failures and interruptions, under the same 50,000-evaluation cap.
The exact cache recomputes owners of added words plus programs whose current
canonical path uses a removed word. Stable pool order proves unaffected paths
remain canonical. Every newly best trial receives a full search-side canonical
rescore, matching all cached paths and costs, before becoming retainable. The
rescore is charged. A soft time/evaluation stop may retain an earlier already
fully rescored best, never an interrupted new best. Record partial/omitted sweeps;
no retry, neighborhood change or inferred completion.

## Limits and failure dominance

Each cohort receives 600 search seconds, 50,000 attempted evaluations, up to seven free
slot sweeps, twelve exchange epochs and top-four swaps. R uses core 4, naming core
5, one numerical thread and 8 GiB RLIMIT_AS per worker. Separate production and
independent report phases each have a 1,200-second whole-phase cap including
preflight, all input hashing, graph construction, witnesses and final publication.
Worker alarms are clamped before contract loading; a BaseException deadline is
not swallowed by ordinary error handling. The supervisor kills worker process
groups and bounds cleanup/log close to a separate ten seconds.

Retain exact parent construction limits: one million arcs, twenty million trie
transitions, two million pool characters; no truncation. Whole-phase failure,
missing worker, stale/mismatched input, uncovered retained source, violated cap,
failed independent replay, cleanup or publication error yields no accepted witness.
Production requires a fresh output directory and refuses to overwrite an old run.
Report failures independently withdraw any stale complete result even if failure
receipt writes or log close also fail. No automatic rerun or budget extension.

## Separate independent replay and reporting

The reporter rebuilds parent identities, source qualification, pool and bans,
reconstructs every retained canonical packet with an independent full-ID DP,
and verifies seed caps, exact ratios and all charges. Replay every retained state,
not only the final state, and reconcile exact source hashes against the public
canonical seed reference. Search cache state is never its decoding authority.

Replay ordered opportunity hashes, shortlist ordering, attempted/completed counts,
rescore-before-retention links, exact strict admission, full/partial sweeps and
stop reasons. Independently recheck each recorded coverage-failure program and
one exact cap-violation witness for every rejected cap trial. One violating program
is sufficient to establish rejection; the additional violation-count field is
explicitly search-only diagnostic evidence. Other rejected feasible trial scores
remain search evidence, not independently certified optimization results. The
report does not rerun search, refit a dictionary or execute source programs.

Report canonical seed/final N,C,C/N, selections/actions quantiles, all per-ID cap
deltas, adjacent-incumbent regressions, full storage, one-owner and >=90%-source
entry shares, population/source/pool hashes, actual timing/peak RSS and retained
failure counts. Minimum-F records are historical comparators only. Public output
contains metadata/hashes, never source/dictionary strings, q, cases or raw output.
Parent unrestricted integer bounds remain historical bounds, not an optimized
canonical-ratio gap or new impossibility result.

Predictions registered after item 44 and the invented proof, before private input:
P1 both cohorts finish with independently replayed covering, cap-respecting states
(expected true); P2 both cohorts strictly reduce canonical C/N relative to their
own canonical seed (expected true, uncertain under the caps); P3 any retained
state reaches C/N<=10% (expected false). Evaluate each separately. A ratio plateau
or lower N/package is not relabeled a strict fraction improvement.

## Evidence already available and launch boundary

The measured prototype, original six tests, synthetic code/spec/receipt remain
byte-identical. The invented 300-string, 75,000-character, maximum-length-400
fixture has 2,048 pool entries and 249 seed entries. One complete sweep plus one
final rescore took 48.252 seconds and 144,040 KiB under a 55-second guard. Production
fully rescores every newly best proposal, so that single-rescore measurement is
not a corpus ETA or production work estimate. Separate focused checks pass: six original prototype tests, five timed-search
tests, four contract/guard tests, three invented runner tests, eleven supervisor
publication/cleanup tests and seven independent-report tests (36 distinct tests).
The reporter includes an invented runner-to-replay pipeline, exact canonical tie
and cap/packet/ratio corruption checks, source-bound parent pool reconstruction,
and timing/RSS/returncode corruption. Supervisor cleanup fault tests use supplied
process doubles; they do not claim an additional descendant execution campaign. No runtime-driven tuning is authorized by this freeze.

After root/Claude review and exact activation, root may invoke the supervisor
with phase=production and a fresh output directory, then phase=report in another
fresh directory only after production completes. The report must succeed before
any evidence record. This pending document grants no launch authority.

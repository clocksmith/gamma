# Proposed item 50 production adapter and independent replay

2026-10-24. Auxiliary design after the [invented measurement](README.md).
This document is not part of the measured synthetic pins. No production code,
private binding, corpus access or launch is authorized by this proposal.
The measured prototype, independent checker, tests, script, specification and
receipt remain unchanged. No second synthetic measurement is proposed.

## Fixed scientific procedure

For each unchanged R/naming 300-fit cohort, use exactly the recorded item 28
integer q with denominator 1000000. Preserve every old occurrence multiplier;
construct new penalties from exact old shortest-path potentials. Compute and
independently replay every k=0,...,256 with capacity 256, charging all paid entries
including singletons. No q optimization, additional starting point, witness,
source rewrite, validation source, case execution or packet claim is added.

The new experiment's informative output is the full conditional bound curve,
especially how far positivity survives beyond k0. k0 dominance over item 28 is
a theorem conditional on replayed identities, not a discovery or a promotion
gate. A nonpositive k256 bound is inconclusive; it does not upper-bound the
best possible dual certificate. Small-k failure can reflect unique characters
rather than semantic reuse. Item 23's later unchanged-source exit 137 remains a
separate inherited failure; exact named item 13 qualification is reused only.

## Predictions registered before private access

- **P1:** Exact L28 equality and k0 dominance over the accepted item 28 bounds
  hold in both cohorts. These are required proof/identity invariants, predicted
  true; failure invalidates the experiment rather than becoming a weak result.
- **P2:** At least one cohort retains a positive bound at some k>=1. This is
  uncertain before the private lift is computed.
- **P3:** At least one cohort has a positive unrestricted k256 bound. Predicted
  false; a negative outcome is inconclusive about the best possible dual bound.

Report the largest positive k in each cohort, or null. Positivity at a support
budget excludes the fraction target in that conditional model; it does **not**
establish that complete coverage is feasible at that budget. No feasibility
claim is made at a larger budget when the bound stops being positive.

## Public provenance already inspected

The item 28 and item 35 contracts have identical 300 fit IDs, cohort paths, raw
fit-source hashes, and pinned `lagrange-select-v2/selection.py` and
`tail-search-v1/structure.cjs` identities. Item33 provides the unchanged full
substring universe between them. The item 28 optional pool has no mandatory
characters; all 96 alphabet entries participate in the256 paid-entry limit.

| Public artifact | SHA256 |
| --- | --- |
| item 28 contract | ff105fe046533e2b08905f1363a749dea62b3eaff5838f9c8df49415f78160cd |
| item 28 accepted evidence | f679214f98d81165e2b54258ffe91287986472e3311b89279ab87bf622a48d25 |
| item 35 contract | 7d61f4ddedd726d1b564df5554986e5bbf86335d69174414c9cede12bebd9cd1 |
| item 35 accepted evidence | 96d7a2b91d8b32a937582561b76df55a6f2036cdd02839e72ea2b73d9b5bf5d6 |

Relative to the already authorized fit work root, the proposed private allowlist
contains **nine exact files**, all hashes available from these public records:

- `binding-descent/run-v1/control-256/fit-sources.json` and `dictionary.json`;
- `binding-descent/run-v1/scope_joint-256/fit-sources.json` and `dictionary.json`;
- `all-length-fraction/run-v1/results.json`;
- `all-length-fraction/run-v1/R-flex256/pool.json` and `certificate-q.npy`;
- `all-length-fraction/run-v1/naming-flex256/pool.json` and `certificate-q.npy`.

The old private result hash is
`b1074bbb30c3aa5a5a34841e77408b00fa0fab4c0a35059a872a7e21885a1096`.
Bind source/seed hashes from both old contracts, pool hashes from item 28 arms,
and q hashes from their accepted integer certificates. Do not inherit item 35's
private item 33 q/results files: they are not inputs to this lift. No400-source
file, validation hash, validation source, oracle case or held-out input is needed.

| Cohort | Old pool hash | Old q.npy hash |
| --- | --- | --- |
| R | fb59efe69f9ba6beed8145f2822d85e1197e9e0dbc6010ae6efcebd9d6412510 | 46bd8eb41228c500e60bdf5bd2d22436cd719bc08e98e7485950563913755766 |
| naming | 129a6d739972cba2927f3c2bbe12e6ee2cce79f9196ee3a900b6b34c97e9fa2f | d4b2edbcae1204117633842559471c7a275b975cbeb86e2b4a8f90c4284edda9 |

## Proposed file deltas

1. `binding.py`: side-effect-free public pin checks and an activated-contract
   private loader. Hash raw bytes before parsing; verify exact per-ID source
   hashes against named item 13 control/scope_joint width 8 receipts and item 28
   and item 35 evidence. Parse old pool and seed without reserializing their
   claimed raw hashes. Load q with pinned NumPy, `allow_pickle=False`, exactly
   one integer dimension and the expected occurrence count; reject floats,
   bools, negatives and shape mismatches. Convert to Python integers with
   `.tolist()` without rounding, scaling or requantization.
2. `production.py`: a new adapter around the unchanged measured `Lift` and
   `certificate`. Rebuild old shared strings, union exact seed extras and96
   characters, then require complete equality to pinned old pool. Compare
   extras count/hash, max length, pool count, old occurrence count and order.
   Assert every old occurring edge survives the full bans. Compare all old
   exact certificate terms before emitting any full-class curve.
3. `run.py`: one bounded worker per cohort. After active-contract, runtime and
   resource checks, load only the allowlist, derive bans, execute the adapter,
   and write private progress/complete/failure receipts. Full rows, exact
   source/pool/q/ban/index identities and phase counters are retained. Any
   partial computation has no accepted certificate or prediction verdict.
4. `report.py`: a separate worker invoking unchanged `independent.check` from
   original pinned inputs, not from stored potentials or top entries. Rebuild
   source and ban identities, old pool and q occurrence mapping, forward paths,
   suffix potentials, full index/support and all 257 rows. Compare all retained
   production terms exactly. Publish only after both arms and supervision
   pass. It must not call the production `Lift` or reuse its selected maxima.
5. `supervise.py`: separate production and reporting phases, fresh output
   directories, checked worker process groups, absolute phase deadlines,
   bounded descendant cleanup and final failure-dominant publication. Parser
   subprocesses stay in each worker's process group. A failed phase cannot
   promote a complete-looking partial arm or leave stale successful evidence.
6. `make_contract.py`, `FREEZE.md`, focused adapter/contract/supervisor/report
   tests: public-only inactive binding first; exact pending equality on
   activation, changing only `active`. Pin measured code/spec/receipt, new
   execution files, imported structural/parser/runtime dependencies, parents'
   accepted evidence and the two exact qualifications. No measured source
   file needs modification to implement this envelope.

## Ban, pool and certificate replay details

Use the exact pinned Node/`structure.cjs` parser contract from28/35, including
full sources and every returned solve definition/body, including primitive
arrow bodies. The new wrapper adds deadlines and process-group cleanup around
that same parse; it does not alter the exclusion rule. Assert exact program
keys and parse shape, form one global set over all 300 sources, and record its
canonical hash and count. The parser is a declared shared dependency of both
execution and replay. No source is executed. After unioning all 96 characters,
check the entire old pool is disjoint from bans, as the accepted28 report did.

Old q ordering is lexicographic string-PID order, then increasing start and end,
not numeric PID order. Rebuild and record the ordered occurrence digest. The
original 28 `per_program_path_numerators` is a list in that sorted order; compare
it elementwise, not merely its sum. Also compare D, old top256 charge, exact
numerator, integer ceiling, pool/edge counts and q raw hash to both old private
results and accepted public evidence. Expected accepted terms are:

| Cohort | L28 | Old top256 charge | Numerator | Integer bound |
| --- | ---: | ---: | ---: | ---: |
| R | 93,534,943,854 | 71,339,305,291 | 22,195,638,563 | 22,196 |
| naming | 78,055,753,489 | 64,331,433,312 | 13,724,320,177 | 13,725 |

Rebuild full item 35 structural counts as additional identity checks: R has
76,107 characters and 13,553,771 allowed entries; naming 76,033 characters and
13,561,646 entries. Both have 111,543 compressed groups and 966 exact banned
occurrences. Counts alone do not prove identity: exact sources, pinned parser,
global bans and item 33's suffix/interval/ban verifier establish the universe.
Do not load or fit item 35 q. The independent checker verifies full suffix
geometry and streams every allowed depth, unlike optimized unique-entry RMQ.

No old/new packet replay is necessary because this task constructs no encoding
or behavioral claim. Reuse only the exact named item 13 qualification receipt;
report zero new qualification jobs and zero new witness packets. Keep potential
arrays, selected entry identities, q and source strings private. Public output
may contain hashes, counts, timing, all 257 numeric rows, maximum certified k
or null, and clearly scoped proof predicates. It must not publish substring
identities, dictionary values, source-derived diagnostic text or test cases.

## Proposed caps and required failure checks

Recommend the root-proposed envelope: **600 seconds per cohort worker,
1200 seconds whole production phase, and a separate 600/1200-second independent
report phase**, with R on core 6, naming on core 7, 8 GiB per process, and at most
10 seconds cleanup. Allocation is queued subject to the owner's availability
check. These are maximum authorized budgets, not an ETA inferred from20.589
seconds on invented strings. Whole-phase accounting includes setup, imports,
pin checks, parsing, all pool/index construction, q replay, aggregation, receipt
serialization and final publication. Worker limits are installed before contract
reading; an explicit BaseException deadline cannot be swallowed by ordinary
exception handling. The supervisor also enforces absolute deadlines and kills
the complete worker/parser process groups. Cleanup time is recorded separately;
no successful result can be published after its active phase deadline.

The measured 75k fixture has 313,344 old entries but 758,605 old occurrences,
versus the actual public28 counts 1,370,583/1,319,319. Its 8,966,636 full entries
differ from the public35 counts above. The 12k fixture exercises 5,991,440 repeated
new-occurrence contributions but has only 101 old entries. Neither determines
the actual combination of costs. Preserve the quadratic worst-case caveat.

Focused implementation checks should cover wrong parent/pool/q/source/ban
identities, reordered old paths, invalid q dtype or dimensions, numeric/bool
receipt corruption, all 257 row omissions and changes, k0 dominance, k256
unrestricted parity, a long child+grandchild timeout, early and post-replay
publication failures, stale-success withdrawal, and inactive-contract refusal
before private reads. No optimization rerun, broad suite or corpus probe is
needed to test these behaviors. Root and Claude must review a concrete frozen
contract before activation or private execution.

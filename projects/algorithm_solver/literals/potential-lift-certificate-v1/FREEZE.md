# Item 50: fixed potential lift and conditional support-budget certificate

Prelaunch protocol, 2026-10-24. This is a new fixed certificate construction
after the [recorded proof and invented measurement](README.md). No optimization,
source change, witness search or source execution is part of this run.
The accepted measured prototype/checker and their eight original pins remain
unchanged. `pending-contract.json` is public-only and inactive until separate
root/Claude review, exact activation and launch authorization.

## Target, population and procedure

The two cohorts are exactly item 28/item 35's original R and naming 300 fit
sources. Evaluate F=10C-N, with C singleton selections and N all selections
excluding Finish. The full universe is every nonempty occurring exact substring
except the unchanged global whole-source/solve-definition/solve-body bans.
Each dictionary has at most 256 paid entries; characters are optional paid
entries. At most k paid entries may occur in exactly one distinct source ID,
including singletons and unused entries. Repeated and overlapping occurrences
within one source do not change its support class.

Preserve exactly the item 28 integer occurrence q, denominator 1,000,000 and
lexicographic string-PID/start/end occurrence order. Rebuild old suffix
distances d. For each newly allowed edge i->j set
`qnew=max(0,d_i-d_j-D*b)`, with b=9 for length1 and b=-1 otherwise.
Every new edge satisfies the old potential inequality; retained old tight
paths establish exact full-path equality at every suffix. Shared entry weights
are unchanged. Compute every k=0,...,256, using exact Python integer top-256
charges and ceiling division. No scaling, q refinement, restart, additional
point, generated vocabulary or proposal-dependent parameter is permitted.

The proof and aggregation algorithm are fixed in measured `prototype.py`.
Unique-occurrence ranges use endpoint minima and best-first splitting;
repeated-one-owner ranges stream exact depths and occurrences. Preserve exact
old multipliers even on slack edges. Do not replace them by smaller potential
penalties. The k0 bound must dominate the accepted item 28 bound; k256 is the
unrestricted full-pool charge at this one constructed q, not a dual optimum.

## Exact input authority

The inactive binder reads only public parent 28/33/35 contracts and accepted
evidence, named item 13 qualification receipts, code/runtime files and the
measured synthetic record. It asserts identical parent fit IDs, source hashes,
cohort paths and source/body-parser pins. It does not inspect private file
existence or contents. `active=False` is required in the reviewed pending file;
activation rebuilds it exactly and changes only `active` to true.

The private allowlist has nine exact files under the approved fit work root:

- the original control256 and scope_joint256 `fit-sources.json` and
  `dictionary.json` (four files);
- `all-length-fraction/run-v1/results.json`;
- the R-flex256 and naming-flex256 `pool.json` and `certificate-q.npy`
  from that run (four files).

Each worker reads only its cohort's four inputs plus the common old result.
Hash bytes before parsing, with hashes copied from accepted public evidence.
No directory walk, private inventory, item 33/item 35 q,400-source file,
validation source/hash, oracle case or protected input is loaded. The old
result's exact raw hash binds its legacy schema, which lacks a top-level
`complete` field; require its two expected arms, capacity/mode, validation=false
and exact parent certificate identity instead of inventing that field.

The q array must be one-dimensional signed64 with the exact expected occurrence
count and no trailing payload, loaded with `allow_pickle=False`. Convert to
Python integers without rounding; reject floats, unsigned values, bools,
negative values and shape mismatch. The raw q hash remains authoritative.

Rebuild all old shared strings, pinned learned seed extras and 96 alphabet
entries. Require ordered pool equality, seed inclusion, no global banned
entry, exact pool/occurrence/max-length/extra counts and hashes. Both accepted
parents have zero learned extras, but no character is made free. Derive bans
through the exact pinned Node `structure.cjs` and `lexical.cjs` code, including
primitive arrow bodies; keep parser descendants inside the worker group.
Source bytes are parsed, never executed.

Compare each source hash to the exact named item 13 control/scope_joint width 8
passed qualification receipt, item 28 and item 35 source identity. Qualification
reuse is the only behavioral evidence; item 23's later unchanged-source exit 137
remains a separate inherited failure. No new qualification, packet or witness
claim is made.

Rebuild full structural counts against accepted35: R 76,107 characters,
13,553,771 entries; naming 76,033 characters,13,561,646 entries; both 111,543
compressed groups and 966 exact banned occurrences. Exact sources, pinned
parser and the independent suffix/interval/ban verifier establish identity;
matching counts alone are insufficient.

## Old and new exact acceptance

Before any result is complete, old q must reproduce every sorted-PID path
numerator, L, top 256 charge, exact numerator, denominator and integer bound:

| Cohort | L28 | Old top 256 | Numerator | Integer bound |
| --- | ---: | ---: | ---: | ---: |
| R | 93,534,943,854 | 71,339,305,291 | 22,195,638,563 | 22,196 |
| naming | 78,055,753,489 | 64,331,433,312 | 13,724,320,177 | 13,725 |

The independent reporting phase reconstructs all inputs and bans afresh and
uses unchanged measured `independent.check`: Aho-Corasick occurrence ordering,
forward source paths, reversed-DAG suffix potentials, old Bellman/tight-edge
checks, same-owner run endpoints, and streaming every allowed depth, including
unique entries. It uses bounded sorted top lists and a separate allocation
loop. Item 33's Index and accepted partition verifier are explicit shared
structural dependencies. It does not call the production Lift or trust stored
potentials/top choices. Compare old terms, source/pool/q/ban identities,
full shape, exact class/top identities and every new row; omissions or unknown
fields fail closed. Scalar top choices are not proposed encoding dictionaries.

Both production workers must exit with actual integer zero statuses, finish
cleanup and log closing, and publish complete receipts. Reporting checks the
whole production result, supervisor and both arm files with no failure before
private opens. It independently checks timing/RSS, input provenance, all 257
rows and scope before publishing. Reports are complete only if both cohorts
pass; no partial certificate or prediction verdict is promoted after timeout,
resource failure, parser error, corruption or failed publication. A report
failure withdraws stale successful results/REPORT regardless of failure-receipt
I/O errors. Fresh phase directories are required.

## Registered predictions and interpretation

- **P1:** Exact L28 equality and k0 dominance in both cohorts, predicted true
  and required as proof/identity invariants. Failure invalidates the run.
- **P2:** At least one cohort has a positive bound at some k>=1; uncertain.
- **P3:** At least one cohort has a positive unrestricted k256 bound;
  predicted false.

Report all 257 numeric rows and each cohort's largest positive k (or null).
Positivity excludes the fraction target under that support budget; it does not
establish coverage feasibility at that budget. A larger budget is not proved
sufficient when the bound becomes nonpositive. Small-k infeasibility may reflect
unique characters. No semantic-reuse, canonical-action, package, source-rewrite,
M1,400/500-population, held-out, or dual-optimality conclusion is authorized.

## Runtime and failure envelope

Two separate phases: production, then independently invoked reporting. Each
cohort worker has 600 seconds; each whole phase has 1200 seconds. R uses core 6,
naming core 7. Each process has 8 GiB RLIMIT_AS and OMP/OpenBLAS/MKL threads 1.
The supervisor sets limits before importing binding code; workers inherit them
before startup and also set literal limits before local imports on standalone
entry. Literal signal deadlines begin before argument parsing/local imports or
contract reads; the remaining absolute phase deadline can only reduce a worker
deadline. BaseException deadline signals cannot be swallowed by ordinary
Exception handlers. Parser children and grandchildren inherit worker groups.

Cleanup kills complete process groups and closes logs. Normal cleanup has a
10-second cap inside the original phase deadline. On first failure, one absolute
emergency deadline is the earlier of failure time plus 10 seconds and phase
deadline plus 10 seconds; if normal cleanup itself fails, its start anchors the
allowance. Cleanup, log closing, success withdrawal and failure publication
share that deadline without resetting it. Every operation checks remaining
time; a hard deadline propagates without starting later writes. No success is published until cleanup completes and
the original phase deadline remains valid. The final receipt/publication also
runs under that original deadline; cleanup cannot extend a successful phase.
Outer supervision and the per-worker signal guard cover input hashes, parser,
pool/index construction, old replay, exact aggregation and serialization.
Failure never silently truncates the pool, reduces k, extends budget, changes
q, retries a cohort or promotes a completed partial arm.

Use the parent's pinned NumPy Python 3.14 runtime (NumPy 2.4.4), with fixed loader
module hashes and pinned Node/Acorn parser. The prior synthetic 20.589-second
measurement is not a corpus ETA. Its 313,344 old entries included 758,605
occurrences, below actual 28's1,370,583/1,319,319; its other fixture stressed
5,991,440 repeated contributions. Preserve the quadratic worst-case limit.

## Evidence and verification

Public output contains only hashes, counts, phase timing/RSS, exact old scalar
terms, all 257 numeric allocation/bound rows, invariant/prediction outcomes and
the named qualification/scope caveats. Sources, q, pools, selected entry IDs,
potentials and source-derived diagnostic strings stay private. No packet
replay is necessary because no new encoding or behavior is claimed.

Focused development checks cover the unchanged mathematical kernels, exact old
parity/geometry drift, signed q dtype/payload validation, primitive arrow bans,
inactive refusal before private access, exact activation drift, post-proof write
failure and real worker/child/grandchild group cleanup. Independent reporter
tests additionally cover all 257/top/identity corruption, timing/RSS/exit types
and failure-dominant publication. Record final test counts with the freeze
handoff. No broad repository or corpus test is implied.

`README.md`, `REVIEW.md`, `DRAFT-NEXT.md` and `REPORT-DESIGN.md` are recording or
auxiliary design documents, outside new execution pins. The original measured
`DRAFT.md` remains pinned by its synthetic specification. Production/replay
implementation, tests, this FREEZE, parent public evidence and required runtime
files are pinned in the pending contract. Component intent is preserved with
no production boundary change or promotion authority added.

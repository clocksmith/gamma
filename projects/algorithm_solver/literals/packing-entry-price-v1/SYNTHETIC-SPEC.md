# Item 71 invented-input measurement specification

This specification prepares a single bounded measurement of the owner-only
packing refinement in [DRAFT-NEXT.md](DRAFT-NEXT.md). It does not authorize a
measurement. No original-fit or private source is an input. The global packing
theorem and the item 68 forced-owner composition are outside this kernel.

## Fixed inputs and computation

Use exactly the two ordered, invented item 50 fixture definitions already
accepted in items 53, 57 and 63: `paired_prefix_75k` (300 sources of length 250,
seed 50065) and `repeated_one_owner_12k` (12 sources of length 1000, seed 50112).
The generator, 96-character alphabet, complete old shared pool plus alphabet,
seed, original occurrence order, original q construction, D=1,000,000 and B=256
remain unchanged. Their input-spec SHA256 is
`a7d7843c947ccf0d8c691086614379cd5ddaa5f918bc50602e7947847f446f25`.

For each fixture, construct the unchanged pool and q, execute production 71,
then execute independent 71. Each side freshly reconstructs its entire unchanged
item 63 baseline, including items 57 and 53/50. Each side also reconstructs the
additional old-potential context needed for the new calculation. That duplicate
work is intentional and charged; historical output never substitutes for a
fresh baseline.

The new owner denominator is `n=min(m,source_length//entry_length)`, with all
allowed occurrences, including zero-q occurrences, counted in m. All 15 prices
are fixed: zero followed by D times powers of two from 1 through 8192. No grid,
source, q or dictionary is selected from the measurement. Production uses depth
segments and a quotient cache keyed by n. Independent replay uses fresh Z
counts, old AC counts and backward interval schedules. It receives the complete
production item 63 baseline plus all new forward vectors, count streams, caps,
packing diagnostics and priced prefixes. Every old 57 forward recurrence,
every old 63 forward recurrence and every new 71 forward recurrence is checked.

Before either large fixture, run all 21 supplied-input oracles: six theorem,
eight production and seven independent tests. They include the actual q53
reconstruction checked against the tiny item 71 theorem, zero/finite capacity,
bans, overlapping occurrences, JSON transport, and rejected corrupt schedules,
counts, caps, identities and packing diagnostics. Import and oracle work is part
of the same budget. Harness fault tests are focused development checks, not
another timed large-fixture campaign.

## Required comparisons and retained evidence

All 257 budgets must independently agree for the new result. Compare the entire
fresh item 63 common science and both directional digest sets with its accepted
invented receipt; compare deterministic production and independent work with
the corresponding old fields, never with each other. Reconcile all historical
50, 53 and 57 rows, old q/pool/source/ban metadata, potential and weight digests,
full shared/owner geometry and deterministic scalar work. JSON keys normalize
before sorting, with strict type and key-collision checks; multidigit budget
keys must survive a real JSON round trip.

Retain rows 50/53/57/63/71, both deltas versus 63 and 57, full per-source price
caps and finite priced prefixes, marginal choices, all count-stream digests,
both directional schedule commitments and all scientific digest sets. Keep
packing diagnostics as occurrence-weighted endpoint counts: eligible owner
endpoints, n<m endpoints, maximum m and n, sum(m-n), and reduced share. Empty
endpoint diagnostics use zero counts/maxima and null share. Do not publish them
as counts of distinct entries or as exact packing counts.

Check work identities explicitly: with K=15, N source positions, P sources and
A allowed owner endpoints, production new residual evaluations and pointwise
old/new checks are K*A; production vector comparisons are K*(N+P), while fresh
independent recurrence positions are K*N. Both sides inspect A new q/count/
packing records. Cached quotient divisions are K times the number of distinct
cached n values; pointwise comparisons also evaluate the old m quotient. Keep
baseline 63, baseline 57, paired 53 and incremental 71 work in separate fields.
Retain pool/q, production, independent and comparison elapsed times; retain the
worker cumulative peak RSS separately from the supervisor peak. No historical
timing ratio is a matched performance estimate.

## Lifecycle and publication

One whole-job limit of 600 seconds starts before remaining Python imports in
the supervisor. The worker inherits that absolute deadline, so preflight,
imports, all oracles, construction, both full kernels, comparisons, serialization
and normal cleanup all consume the original budget. Both processes are pinned
to core 6 with OMP/OpenBLAS/MKL thread counts one and an 8 GiB address-space limit
per process. The two process limits are not an aggregate 8 GiB limit.

The worker runs in its own process group. Normal cleanup kills the group before
blocking wait, log close or output withdrawal; success is published only after
cleanup and within the original deadline. A failure has one absolute cleanup
allowance, ending at the earlier of first failure plus 10 seconds or original
whole deadline plus 10 seconds. A normal-cleanup failure uses that cleanup's
original start. No operation refreshes this allowance. An expired deadline is a
BaseException and cannot be swallowed by ordinary failure-write recovery.
Failed or partial work has no accepted result. Existing output directories are
refused without modification. Final complete results are replaced last, after
the report and supervisor receipt; any publication failure withdraws success
under the remaining absolute failure budget.

## Preparation and authority inventory

`make_synthetic_spec.py --output <reviewed-path>` only prepares pins. It does not
launch anything. Do not invoke it until root authorizes preparation; a resulting
spec is still not launch authorization. The eventual launch must supply the
reviewed spec SHA256 explicitly. The harness reconstructs the public spec and
checks exact equality and all hashes before any fixture computation.

The explicit local inventory is `DRAFT.md`, `DRAFT-NEXT.md`, `proof.py`,
`test_proof.py`, `caps.py`, `test_caps.py`, `independent.py`,
`test_independent.py`, `synthetic.py`, `test_synthetic.py`,
`make_synthetic_spec.py` and this file. Inherit the exact accepted item 63 code
and runtime closure, including its item 57 ancestry; bind accepted 57 and 63
specs, results and supervisory receipts. Additional tiny theorem dependencies
are the unchanged item 66, item 68 and item 61 proof modules. These are oracle
mathematics only: no item 66 execution kernel, loader or reporter is imported.
Runtime pins include the resolved interpreter and the explicit standard-library
modules used by this harness, together with the inherited runtime closure.

Only `worker-results.json` and status artifacts may precede acceptance. The
supervisor writes final `results.json`, `supervisor.json` and `REPORT.md` after
all checks and cleanup. Successful invented evidence establishes correctness
and measured work for these two fixtures only. It establishes neither corpus
runtime nor a positive full-class bound, coverage feasibility, witness,
readiness or M1 acceptance.

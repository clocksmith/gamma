# Batch five independent reference preparation

This directory owns the 47 explicitly delivered problem identities in
`authored/downloaded-general47-v1`. It is source preparation, not an executed
qualification or canonical admission. The reference author read the assignment
metadata and official public definitions, but no delivered solution bodies or
delivered expected outputs. Original sources and historical protected datasets
remain unchanged. No candidate has run through this lane.

## Definition and identity gates

`contracts.json` binds the imported assignment/manifest and official response
metadata. Forty responses contain a public definition whose frontend identity
matches the assignment. IDs 562,616,625,634,651,681 and 694 return premium-only
metadata without definition content. They remain assigned but blocked, not
qualified, and are absent from the executable case dictionary. There is no
guessed premium contract or fallback to historical protected text.

The supplied 634 slug `find-the-derangement-of-numbers` returned no question.
The canonical official `find-the-derangement-of-an-array` response independently
identified frontend 634, but its content is still unavailable. Correcting the
identity does not clear its definition gate. Full statement responses stay in a
private local directory; only their URLs, availability and exact hashes appear
here. `cases.build(statement_directory)` verifies those hashes before reading
examples. `build()` without statements is for synthetic development checks only
and cannot satisfy that gate.

## Independent references and comparisons

References enumerate division trees with exact rational arithmetic, digit
multisets, contiguous intervals, permutation orbits, deletion subsequences,
triangles, scheduling states, cross-array pairs, graph-edge removals and exact
partition covers. Other references use counted paths, geometric orderings,
explicit rectangles, atomic exclusive-time intervals, shortest quantity-state
paths, equation coefficients, root matching and integer knight-path counts.
Senate outcomes use a bounded optimal opponent-ban tree rather than a queue
implementation. These choices were made without inspecting the candidates.

The test module cross-checks them with different constructions, including prefix
counts, cycle decomposition, LCS, greedy certificates, union-find, bucket
assignment, memoized backwards probabilities and actual button-state reachability.
It includes wrong-value/type/effect/alias and malformed-domain controls.

553 accepts a legal, optimal, minimally parenthesized division expression with
the original operand order, not equality with one chosen expression. 609 compares
complete duplicate-file group membership and multiplicity while allowing both
group orders. 688 accepts a finite real number (Python integer or float, excluding
booleans) within local absolute/relative tolerance1e-12. The pinned definition
does not specify a tolerance; this is an explicitly local numerical envelope.
All other outputs use recursive typed equality. The local functional interface
requires unchanged argument values and fresh mutable return containers, including
nested containers. This does not establish official `Solution` wrapper behavior.

Generated cases retain the public numeric bounds and stated structural promises.
`validate_generated` checks the generated families; it is not a general-purpose
parser for every possible public input spelling. In particular609 cases use the
ordinary unambiguous directory/file-content token format. The complete public
definition remains pinned, and no narrower generated family replaces it.
Reference work budgets raise separately from input-domain validation. Tests and
analytic boundary certificates do not prove correctness on all legal inputs.
The optional linear-time follow-up for 581, heap follow-up for 692 and real-file
system follow-ups for 609 are not converted into mandatory algorithmic gates.
Source-specific complexity review is still pending; no solution body has been
inspected to claim that it satisfies those requirements.

## Cases, transport and future execution

The pinned public-definition build currently generates 27,679 distinct cases
across 40 problems, including 92 official examples and 52 isolated boundary cases.
Exhaustive small families and deterministic seeded cases remain separately labeled.
Large cases use explicit certificates where the enumerative reference budget is
too small. Examples include maximum permutation cycles, full row/word/array
counts, cooling schedules, table extrema and complementary partition pairs.
Not every maximum-shape combination is covered. Full statement snapshots and
generated case/observation payloads are not committed here.

`cases.batch_plan` is a new prospective frozen batching policy. The packet format
is the existing value observer's `entry: solve` and argument-only calls; expected
outputs stay on the host. Normal groups contain at most 32 distinct calls and
repeat their first call. Isolated boundaries normally repeat themselves.
The new policy bounds host packet bytes prospectively at 16 MiB and projects
successful observations against the existing 16 MiB output bound. If a repeated
large call would exceed either bound, a small existing same-problem probe brackets
it in the same interpreter: `[probe, large, probe]`. A single case that still
cannot fit fails closed; it is not silently dropped or reclassified as qualified.
The current batch05 cases fit without bracketing, including packets over 1 MiB.

The sandbox's `max_file_bytes` default of 1 MiB is child `RLIMIT_FSIZE`, not a limit on
host-created input files. The host writes those files before the child starts.
This preparation does not claim older runs enforced a 1 MiB input limit and does
not raise any existing child resource cap. The 16 MiB host packet budget is a new,
explicit prospective planning policy. Projected successful-output lengths are
conservative estimates, not guarantees about arbitrary candidate output; the
unchanged live output monitor remains authoritative.

This policy is not byte-identical to the earlier batch04 plan. A future fixed
cohort preparer must explicitly bind this policy, helper hashes, exact sources,
interfaces, public definitions, generated cases, batch plan and actual Linux
runtime before executing. Reuse the existing sandbox/observers; introduce no
unsandboxed fallback or alternate engine. Existing prospective constraints are
three CPU seconds, eight wall seconds, 1 GiB address space, 1 MiB child-written regular-file
limit and the existing 16 MiB output bound. This preparation changes none of those settings
and does not establish that a candidate fits them.

The future runner must select exactly the 40 `cases.IDS`, retain the seven failed
definition gates, and use `cases.batch_plan` and `cases.packet`. It must save raw
streams before judging and replay observations independently. No source repair,
catalogue insertion, retrieval qualification or held-out claim follows from these
files or their synthetic tests.

## Focused source-free checks

From this directory:

```sh
python3 -m unittest -q test_oracles
```

Current snapshot verification must use the live-gated controller below. The
original 40-ID reference preparation is historical evidence, not current access
authority; do not reopen its nine reserved definition snapshots.

These commands execute only host references and synthetic tests. They do not
import or run a delivered program.

## Fixed runner preparation (prospective; no execution in this change)

`qualify.py` exposes `prepare`, `review-template`, `freeze`, `run`, and `replay`.
It delegates boundary authorization, no-follow bounded reads, Linux runtime
inventory, strict observation parsing and sandbox execution to existing owners.
It does not enroll this batch in the separate continuation A/B populations.
The original authoring assignment/manifest remain the source inventory authority.
Supply `--source-root` pointing at a checkout containing their exact pinned bytes;
source locators cannot be overridden or expanded. The seven blocked premium IDs
are never source-opened or dispatched by this controller. Nine further IDs are
reserved and excluded from all payload opens: 556, 565, 583, 592, 621, 624, 646,
680 and 684. `execution-selection.json` pins the metadata audit identity; live
checks still apply to every allowed open. The prospective selection is 31 IDs.

`prepare --source-root ROOT --gate GATE --gate-sha256 SHA --statements NEWDIR`
refetches only fixed official public URLs after fresh source/statement decisions
for both languages. It requires exact original response bytes; a changed public
response is retained and blocks preparation pending explicit reference review.
It never silently accepts a rewritten snapshot identity.
`review-template` takes those source/gate arguments and `--review NEWFILE`, checks
source/contract pins and emits 62 false-by-default review records.

Before dispatch, an independent reviewer must approve exact-bound source
independence/safety, interface/domain and independent references/boundaries.
Finite-suite qualification additionally requires all seven mandatory fields: source independence/safety, exact
functional interface/domain, numeric behavior, mandatory complexity, effects,
and independent references/boundaries. Each record binds the source, semantics,
reference, case generator, public definition/API, observers and prospective batch
policy. Public presence and cross-language agreement do not satisfy these flags.
All 31 reviewed JS candidates have object exports and use the existing declared
`imported-commonjs-observer-v1/harness.cjs` profile plus the unchanged shared effect
observer. Direct-function transport is not interchangeable. Python `solve` binding
also needs source review; official `Solution` wrappers are not qualified here.

`freeze` additionally needs `--statements DIR --preflight LOG
--preflight-sha256 SHA --review FILE --freeze NEWFILE`. It requires the actual
Linux sandbox/runtime and exact passing existing 37-check judge preflight,
freezes the generated cases, all batch plans, source/helpers/runtime hashes,
six trust anchors and manual reviews. This Mac cannot produce that freeze.
`run` requires `--freeze FILE --freeze-sha256 SHA`, the source/gate/statements
arguments, and a new `--output DIR`; runtime and exact execution gate must match.
A missing dispatch review blocks that program with zero calls and cannot pass.
A false mandatory complexity/numeric/effects gate may retain a safe bounded
observation after safety/interface/reference approvals, but can never qualify.
The independent reviewer identified Python 695 recursion depth risk on a legal
50-by-50 all-land grid; do not mark its mandatory complexity/resource gate true
without evidence, and retain any future actual sandbox failure. Each
sandbox dispatch rechecks live source access, exact bytes and observer hashes.
Expected values stay on the host. Raw stdout/stderr and process status are
written immutably before any candidate verdict; failures remain evidence.
`replay` takes the same arguments but never invokes sandbox execution, regenerates
cases and summaries, and verifies original raw streams, starts, process status,
source/input/runtime identity and aggregate report. A relocated replay gate may
have a different descriptor hash only with unchanged six trust anchors.

The original reference phase prepared 40 public-definition problems; that does
not grant access. The new permitted prospective plan has 31 problems / 62 possible
language reviews, 24,519 unique cases per language, 824 interpreter batches and
25,343 calls per language. No program is approved merely by inclusion.
The largest measured input packet is 2,000,065 bytes; conservative projected
successful output peaks at 4,004,480 bytes. The explicit prospective host-packet
budget is 16 MiB. The existing child regular-file write RLIMIT remains 1 MiB;
it is not a host input-file cap. Existing stdout/resource limits are unchanged.
These are finite development cases, not a universal resource or unseen-domain
proof. No actual candidate execution, new qualification or adoption is reported.

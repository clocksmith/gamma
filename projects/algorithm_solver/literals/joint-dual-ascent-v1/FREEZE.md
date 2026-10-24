# Item 45 proposed execution freeze — 2026-10-23

Pending root and Claude review. Contract activation is a separate final step.
No private inputs have been opened to prepare this freeze or its binding.
The measured prototype, synthetic job and test file retain their exact hashes
in [synthetic-spec.json](synthetic-spec.json). Production is a new wrapper.

## Target and authority

Two independent cohorts use the exact item 42 R/naming 300 fit sources. All
allowed exact substrings, including singletons and one-owner strings, remain in
the full pool, excluding the complete-source/body bans across the entire named
cohort. Capacity is at most 256 **paid** entries, with no free character fallback.
Every longer edge costs −1, every singleton 9, so the path objective is F=10C−N.

N counts selections excluding Finish. The exact conditional family satisfies
arithmetic median N<=32 and nearest-rank p95 N<=96, alongside aggregate C/N<=10%.
Positive verified bounds exclude only this fixed-300 joint target. They do not
exclude M1 or any 400/500-program target. There is no new qualified source,
dictionary witness, reusable-language claim, publication or promotion.
No validation, held-out source, private case, source alternative, parent q or
training data is loaded. Public item 13 qualification hashes bind every source.

## Frozen finite search

Use item 35's 11 start/length-bin multiplier coordinates and denominator
D=1,000,000. Initialize q=0 only. Its joint numerator must exactly match the
pinned, independently replayed item 42 q=0 numerator for that cohort.
Evaluate at most **16 q points**, hence at most 15 updates. For iteration t=0..,

```text
r_t = ceil_sqrt(t+1), computed with integer arithmetic
s_t = max(1, D // (4*r_t))
q_next = max(0, q + s_t*g), coordinatewise
```

Here g is an exact concave **supergradient**: used occurrence indicators for
one exact minimizing joint path family minus all-occurrence multiplicities of
an exact top-256 distinct-entry selection. The bound is
`B(q)=min_joint_paths sum(D*b+q) − top256_all_occurrence_weights(q)`.
Its global supergradient inequality is B(q')<=B(q)+g·(q'−q).
The initial scale gives a +1 occurrence direction a quarter-unit edge multiplier
change and decays deterministically. No L2 normalization, line search, adaptive
parameter adjustment, restart or Polyak/seed upper bound is permitted. The
finite integer schedule is not a convergence or optimality claim. Objective
decreases are allowed. Keep earliest q on exact best-numerator ties, including
the initial zero checkpoint.

The exact median union enumerates every a=1..32 with category caps
a,64−a,96,unrestricted and quotas 150,1,134,15. Solve each integer assignment and
retain its primal labels/dual potentials or Hall cut; choose smallest a among
minimum values. Missing cases cannot be silently skipped. Unexpected empty
joint-family feasibility fails because the pinned item 42 baseline is feasible
in this same relaxation, independently of q.

For an assigned cap, use the smallest k attaining d_p(cap), then recompute that
program's exact layers 1..k. Store only compact uint32 endpoints for one program
at a time and rolling cost layers. The explicit endpoint cap is **64 MiB**;
fail before allocation if exceeded. No edge/source truncation is allowed.
Recover uncapped paths separately. Check whole-source coverage, exact global
bans, path cardinality and exact integer equality to the assigned cost and
global assignment optimum. Negative longer-edge costs are safe in the DAG.

Top-entry ties use inherited piece index, then shortest legal lengths within a
piece. Every selected distinct length counts; interval range additions recover
the full selected-entry occurrence multiplicity. Check both dot-product terms
against the exact path/dictionary costs. Do not collapse a selected piece into
one activation. Stop early only for zero supergradient or unchanged projected
q, retaining the explicit reason. Neither diagnostic is reported as proof of
primal feasibility or optimization convergence.

## Retained targets and independent report

Write complete q=0 and current-best q/proof checkpoints privately; the final
accepted target is the earliest maximum of the finite completed trajectory.
An incomplete search cannot promote its checkpoint. Retain other per-iteration
hashes, objective values, selected a, gradient norm, step, movement flag, phase
times and endpoint bytes as **search diagnostics**, not independently verified
trajectory certificates. No q, string, path, assignment or potential is public.

Independent reporting rebinds source/code/runtime hashes and qualification,
rebuilds the entire allowed substring pool, verifies ban endpoints and top-256
multiplicity, recomputes capped costs using item 42's separate segment-tree DP,
and checks all 32 exact assignment primal/dual or Hall receipts for q=0 and final
best. Identical q/proof pairs may be verified once. The best q digest, numerator
and selected a must match its earliest maximal trajectory row; the zero target
must match pinned item 42. The independently verified best cannot be below the
verified q=0 bound; either bound can remain negative.
No gradient search or solver is rerun by the reporter, and other trajectory
values remain explicitly unverified search diagnostics. No seed gap is reported.

## Resource and failure contract

Production and independent replay each receive a separate **1,200-second whole
phase cap**, including preflight, fit-only source loading, pool construction,
computation, checkpointing and final publication. R runs on core 4 and naming
on core 5, one core/8 GiB per worker, numerical thread environment fixed to one.
The supervisor independently kills worker process groups on any failure/deadline;
cleanup has a separately bounded ten-second allowance. Worker timers start before
contract loading and are clamped to 1,200 seconds even for malformed deadlines.

Each phase requires a fresh output directory. Any input/hash mismatch, bad proof,
coverage error, missing point without a registered early stop, memory/deadline
failure, cleanup failure or publication error produces no accepted overall
certificate. Preserve private failure/progress artifacts. Reporting withdraws
stale successful metadata and prose on failure, including refused reruns. There
is no automatic retry, extra budget, altered population or partial-best promotion.

## Predictions registered after item 42, before private input

P1: both cohorts finish the registered search or registered stationary stop and
both retained targets independently replay within the limits (expected true).
P2: at least one cohort's best exact numerator strictly exceeds its q=0 baseline
(expected true, uncertain; integer lower bounds may still tie).
P3: at least one cohort has a positive independently verified final-best joint
lower bound (expected false).

Report each independently, source counts/hashes, exact and integer target bounds,
best iteration, all registered stop reasons, search-diagnostic scope, actual phase
times/peak memory and unchanged conditional scope. Do not replace this protocol
based on early trajectory values.

`make_contract.py` reads only public metadata to produce `pending-contract.json`.
After pushed freeze and cross-review, activation rebuilds and compares the entire
pending payload and all existing code/runtime pins, then changes only active to
true. Neither binding nor activation opens private input files. Execution and
report loading require active=true. No launch is authorized by this draft alone.

# Item 33: all-substring character-fraction relaxation

2026-10-23. Frozen execution contract after root and independent synthetic
review; launch awaits Claude review and release of item 30 cores 0/1. No corpus access occurred during design. This is the
next candidate-space extension after item 28; it does not alter that run.

## Fixed question and populations

On the two original item 13 fit-only populations, can any dictionary of at most
256 exact literal entries attain C/T <= 10%, where C is single-character
selections and T is all eight-bit selections? The objective is F = 10C - T.
Only a positive independently replayed integer lower bound rules this out.

Use exactly the 300 fit IDs and source hashes inherited through
[item 28's contract](../all-length-fraction-v1/contract.json): R/control-256 and
naming/scope_joint-256. Load only each `fit-sources.json` and seed dictionary.
Check every selected source against the pinned item 13 qualification receipt.
No source execution, rewriting, validation source load, protected population
access, ledger/catalog write, promotion, training, publication or deployment.

## Complete candidate class and mathematical restriction

All nonempty exact substrings occurring in at least one selected source are
eligible, at every length, except the frozen complete-fit-source and extracted
solve-definition/body bans from the inherited `forbidden_strings` procedure.
One-owner entries are included. Occurring characters are optional entries
charged against the same 256 slots. There are no mandatory entries, length
ceilings, top-k pool cuts, occurrence caps, or source exclusions. Unused seed
entries are removed without changing its encoding objective.

[DRAFT.md](DRAFT.md) gives the derivation and complete implicit representation.
All occurrence constraints at the same source start share a multiplier.
This restricts the dual family while preserving the full primal substring
space. For q >= 0 and D = 1,000,000, the certificate is

    ceil((sum exact relaxed path numerators - top-256 word weights)/D).

A compressed suffix-array interval/depth group stores all words sharing the
same occurrence-start set, with exact multiplicity after bans. Top-256 selection
counts multiplicities, including many alternative lengths in a one-owner
group. This can make the start-tied bound weak: a nonpositive result is
inconclusive about primal reachability, even when no actual dictionary reaches
10%. A future length-binned/group-sensitive dual is outside this run.

## Fixed search and witness procedure

- Start every multiplier at zero. Each iteration quantizes lambda by floor to
  nonnegative Python integers q, computes the exact heap-DP certificate, and
  retains the strictly best numerator; ties retain the earlier iterate.
- Use the exact minimizing path's start indicator minus the selected words'
  occurrence counts as the dual ascent supergradient. Group selections are
  ordered by decreasing weight then deterministic group ID. Path ties choose
  the smallest endpoint. Selected multiplicities use suffix-rank range adds.
- Theta starts at 1 and halves after 30 iterations without a strict improvement.
  The projected step from q/D is theta*(upper - current bound)/squared gradient
  norm. The feasible seed or a strictly improved generated dictionary supplies
  the upper bound. Reject nonfinite/negative multipliers. No random restarts.
- Every 25 iterations, including iteration zero, try two dictionaries from
  selected groups: the shortest allowed depths and the longest allowed depths.
  Within each group, use increasing or decreasing depth, respectively, skipping
  exact bans. Each contains at most 256 distinct words. Evaluate the inherited
  exact min-F encoder with its fewest-selection/entry-ID tie rules. Incomplete
  coverage is an infeasible attempt; no uncharged repair is added.
- Retain seed, best feasible, and best generated dictionaries. Stop at 2,000
  completed iterations, at the first iteration boundary after 1,200 seconds of
  ascent, zero gradient norm, or equality of integer lower and feasible upper
  bounds. Zero norm is labeled `restricted_dual_stationary`; only bound/upper
  equality is labeled `exact_primal_optimum_certificate`. The hard whole-job
  cap below also covers an expensive last iteration.
- Before accepting a worker result, independently validate suffix order/LCP,
  all interval/depth groups, full distinct-word count, every exact ban and
  top-256 multiplicity. Independently replay integer paths using a segment
  tree and compare the exact numerator. No floating-point tolerance is evidence.

## Resources and failure behavior

Two queued workers: R on core 0, naming on core 1; OMP_NUM_THREADS=1 and
OPENBLAS_NUM_THREADS=1. Each worker has an 8 GiB address-space limit. The
`supervise.py` deadline is 2,400 seconds from job start and covers metadata and
private hash checks, worker loading, bans, suffix construction, all ascent,
independent replay, exact packet/cost output and final aggregation. Each worker
also receives that same absolute deadline and an alarm. The supervisor kills
both worker process groups, including parser descendants, on any failure.
Python optimized mode and PYTHONOPTIMIZE are explicitly rejected.

Memory failure, timeout, process error, missing coverage or certificate mismatch
leaves a failure record. No implicit group or ban is clipped and no partial
worker result is promoted as a completed whole-job certificate. All artifacts
remain private under the selected fresh output directory.

## Recorded outputs and independent report requirements

Private artifacts: traces, q JSON and hash, exact bound accounting, group/word
counts, source identities, seed/best/generated vocabularies and encoded packets,
per-program costs, complete dictionary/packet/decoder storage, entry length and
one-owner counts, runtime and retained failure records. No source strings,
vocabulary entries, packet sequences or multipliers enter public evidence.

An independent report must reload the pinned fit-only sources, rebuild the
implicit index and exact bans, verify the q hash, replay the integer certificate,
and independently decode/recount every reported witness packet and cost. It
must check exact source hashes against the pinned qualification receipt and
require the supervisor's complete result. M1 semantic reuse is unassessed:
near-whole/one-owner chunks passing exact bans are relaxation witnesses only.
Source bodies cannot be disguised as helpers to claim a milestone.

## Registered predictions and acceptance checks

Predictions, recorded before any corpus query:

1. Both arms finish at least one independently replayed certificate within the
   hard resource caps, without materializing the quadratic distinct-word pool.
2. At least one arm has a positive integer lower bound. This is a low-confidence
   scope-extension hypothesis; the start-tied multiplier restriction may make
   both bounds nonpositive despite the positive shared-pool item 28 results.
3. Neither arm's generated dictionary reaches F <= 0. Any counterexample must
   be reported with exact decode/cost evidence and an explicit unresolved
   semantic reuse audit, not suppressed or called M1-qualified.

Acceptance requires full-pool partition proof, exact integer replay, fit-only
source identity, explicit complete/failure status, all witness costs, and an
honest prediction verdict. No prediction is required to hold for a valid run.
A positive bound applies only to the named fixed 300-source population and
its full-substring class; it does not close M1 on 500, other rewrites/subsets,
quantile gates, human fluency, autonomous solving, or publication rights.

## Synthetic checks and provenance

Eleven tests pass under system Python before freeze: 180 randomized full-pool
and old explicit-dual comparisons, 40 exhaustive tiny dictionary searches,
repetition/prefix/duplicate suffixes, exact bans, one-owner/near-whole words,
large integers, corruption rejection, bounded optimizer checks, and actual
worker process timeout/failure checks. The tests open no research corpus.
The same eleven focused tests also pass under the pinned Python runtime.

`make_contract.py` inherits existing private-file identities without opening
private files, hashes only code/docs/runtime metadata, and records this freeze.
Component intent is preserved; no component boundary or owner gate changes.

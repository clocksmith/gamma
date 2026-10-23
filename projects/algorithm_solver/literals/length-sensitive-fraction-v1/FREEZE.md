# Item35 prelaunch freeze: length-sensitive full-substring fraction dual

Prelaunch freeze for root/Claude review. No private input has been opened for this design;
no execution follows from this document alone. Item33 recordedc8ed60959 is the
immutable parent. [DRAFT.md](DRAFT.md) gives the proof and independent algorithms.

## Disclosed adaptive starting evidence

Item33 independently replayed R/naming bounds−37980/−37943, retaining all-zero q;
13,553,771/13,561,646 allowed words,111,543 compressed groups each,320 infeasible
generated dictionaries,308.60 seconds whole run. Item35 was designed after this
result. Its predictions do not predate it. These nonpositive bounds were
inconclusive, not evidence that a256-entry dictionary reaches the fraction gate.

## Fixed inputs, dual and initializer

Reuse the exact item33 R/naming fit populations:300 pinned IDs each, item13
control256/scope_joint256 sources, identical seed dictionaries and exact
whole-source/solve-body bans. Preserve the entire all-length/one-owner allowed
substring pool; every character also costs an entry. No validation, protected
inputs, source execution, rewriting, pool pruning or source exclusions.

Freeze eleven inclusive bins:1;2;3;4;5–8;9–16;17–32;33–64;65–128;129–256;257+.
One nonnegative integer q per source/start/bin; D=1,000,000. Capacity256;
F=10C−T. Exact bound is ceil((relaxed integer path sum−top256 distinct-word
weights)/D). Piece multiplicities and all exact banned endpoints are counted.
Segment-tree production DP and independently reconstructed per-bin heap replay
must agree. No O(N²) word inventory or floating-point certificate.

Pin item33’s public evidence, private aggregate identity and q hashes by inheriting
public metadata only. At execution, read and verify those files and source
qualification hashes, rebuild the identical pool and independently replay the
old q. Lift q identically into all11 bins and verify exact equality of numerators,
path accounting and top256 penalty. Retain this certified lift as initial best.
The larger family admits it exactly; this does not promise a strict finite gain.

## Search fixed before item35 source exposure

1. From the immutable initial lift, in ascending bin order, try only that bin
   halved with integer floor, then zeroed. Deduplicate exact coordinate identities,
   including the baseline; record all22 dispositions. Retain strict numerator
   improvements only. Item33’s disclosed zero initialization predicts all22
   releases will duplicate the baseline; do not call these new evaluated points.
2. Start projected ascent from the best retained diagnostic/lift. At most2,000
   iterations or1,200 seconds from optimizer entry, including seed checks,
   initializer replay and the release sweep. Check time at diagnostic/iteration
   boundaries; the whole-job guard also bounds a last expensive operation.
3. Theta=1; halve after30 consecutive iterations without strict best-numerator
   improvement. Gradient is full source/start/bin path-use minus selected-entry
   occurrence counts. Update from the exact q/D point by the Polyak step
   theta*(feasible_upper−current_exact_numerator/D)/squared_gradient_norm, project
   to nonnegative reals, then floor at D for the next exact point. Reject
   nonfinite numbers. No restarts or adaptive schedule changes.
4. Every25 ascent iterations including zero, materialize at most256 entries using
   shortest allowed depths, then longest allowed depths within selected pieces.
   Use the inherited min-F encoder with fewest-selection/entry-ID ties. Missing
   coverage is an infeasible attempt; count it, preserve the trace, add no repair.
   Keep seed, best feasible and best generated dictionaries. No witnesses are
   attempted for duplicate or evaluated release-sweep points.
5. Stop at iteration/time boundary, zero norm (`restricted_dual_stationary`) or
   equality between the verified integer lower bound and a feasible upper bound
   (`exact_primal_optimum_certificate`). Only the latter equality certifies an
   optimum. Retain best q and certificate checkpoints; the completed result
   must not be weaker than the initializer. Ties retain the earlier point.

## Resources, queue and failures

Two workers: R core14, naming core15, only after Claude confirms allocation.
OMP/OPENBLAS/MKL threads1. Each worker has8GiB RLIMIT_AS. Supervisor limits the
whole job to2,400 seconds from preflight through loading, bans/index construction,
optimization, independent replay, witnesses/packets and aggregation. Workers get
that same absolute deadline. Failure/timeout kills both process groups including
ban-parser descendants; retain every partial artifact and reject whole-job
promotion. No restart under this frozen identity. Assertions must stay enabled;
optimized Python and PYTHONOPTIMIZE are rejected explicitly.

Execution uses pinned Python through `supervise.py --work <private-root>
--output <new-private-run>`. Independent reporting is a separate rerunnable
operation, `report.py --run <private-run> --work <private-root>`; it does no search.
Its elapsed time is separate from execution. Source/q/private-result files stay
unopened until reviewed launch. Contract generation reads public metadata only.

## Evidence and predictions

Reporting must independently verify input/source/qualification hashes, parent
private aggregate identity and old certificate, complete pool/pieces/bans,
new integer certificate, trace accounting and every witness packet/entry ID/cost.
Charge complete dictionaries, packets,41-byte headers, Finish and both decoder
sources, with per-program and aggregate costs. Installed runtime footprint is
unmeasured. Report one-owner support, lengths and near-whole flags; exact bans
are necessary but not a substantive M1 semantic-reuse audit.

Failure dominates stale success artifacts. Reporting writes explicit incomplete
metadata with no accepted certificate when execution or verification fails.
Public artifacts contain metadata only: never sources, vocabulary strings, q,
packet sequences or raw traces. Retain the inherited item23 later exit137 failure
as separate evidence; item13 exact-hash reuse does not erase it.

Registered predictions, after item33 but before any item35 source access:

1. P1: Both arms complete and independently replay within the hard limits.
2. P2: At least one arm strictly improves the exact numerator over its item33 lift.
3. P3: At least one arm yields a positive integer lower bound (low confidence).
4. P4: Neither generated dictionary attains F<=0.

Predictions are evaluated separately from acceptance. A positive bound excludes
10% only for this fixed-source full-substring class. Zero/nonpositive is
inconclusive; a witness is not automatic M1 legality. M1 remains400/500,<=256
shared entries, median<=32/p95<=96 selections,<=10% single-character bits,
zero whole-solution entries. No generalization, source-rewrite impossibility,
human/autonomous solving, publication or owner-gate claim. Component intent
and protected boundaries are preserved.

## Focused implementation checks

Fifteen synthetic tests pass: nine mechanism/proof tests plus optimizer release,
retention, exact-optimum, process timeout/error and independent artifact-report
checks. The complete report fixture uses300 invented sources in each cohort;
corrupted q/cost/packet data and failed execution are rejected. These checks
are implementation evidence only, not a private-corpus run or qualification.

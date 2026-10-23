# Item 40 prelaunch freeze for review

The [design](DRAFT.md) fixes the population, candidate construction, objective,
proof, model limits and interpretation. The [contract](contract.json) is bound
to the independently recorded item 35 public evidence at `a0f43fc3b`, using
only public metadata. This is ready for root and Claude review; approval and
resource scheduling remain required before launch. No private source/q/result
probe was performed or is authorized during preparation.

Run scope: fixed 300 fit programs for each R/naming source cohort, no
validation, no source rewriting or execution. Capacity 256 includes every
singleton. A protected measured seed plus the two item 35 top-weight endpoint
realizations enters a pool of at most 2,048 words; deterministic relaxed-path
ranking fills its remaining slots. Exact bans remain, one-owner/near-whole
strings are admitted only as a clearly labeled relaxation. No M1 promotion.

Warm/cold share the exact full sparse matrix, objective, capacity, bounds and
candidate order, which are hashed before and after each solve. R runs warm then
cold; naming cold then warm. Each receives 600 solver seconds, one thread and
the same random seed 400. Warm provides the verified minimum-F seed point;
cold provides none. A feasible output must independently decode all 300
sources and pass exact objective rescoring; warm nonregression is mandatory.
No result is silently replaced by a fallback. Cold feasibility is recorded.

Cores 14/15 for R/naming respectively, queued until available, with 8 GiB
address-space cap per worker, 2,400 seconds per
cohort including preflight/construction/replay, and 2,500 seconds for the outer
job including both workers. OMP/OPENBLAS/MKL thread counts are all 1. Guards
cover all phases; the parent separately enforces each worker's deadline even
inside native solver calls. Failure kills complete worker process groups. Construction
limits: 2 million candidate characters, 20 million trie transitions and one
million occurrence arcs. Breaches are failures, never truncation.

The existing item 26 HiGHS adapter is reused unchanged. Only the recorded item
35 full-substring certificate is an independently checked exact lower bound
for that full class. HiGHS floating dual bounds and optimal statuses concern
the restricted proposed pool and remain numerical solver evidence. They do not
establish full-class exclusion of a 10% character fraction. Exact witness
coverage, F/C/N, framing, Finish, dictionary/decoder bytes, per-entry support
and one-owner/near-whole diagnostics are independently replayed. Item 23's
failure remains recorded; source correctness relies only on the pinned item
13 exact source-hash passing receipt, with no fresh execution claimed.

Public outputs are hashes, numeric counts, fixed enums, costs and interpretation.
Sources, q, candidate strings, dictionaries and packets stay private. The
reporter is separate and unpinned, with synthetic corruption/failure checks.
Replay checks HiGHS optimal-status consistency, solver time within measured
call time plus a 0.05-second independent-timer tolerance, and total solver-call
plus model-build time within cohort elapsed time. A replay failure overwrites
both evidence and any previous successful README with explicit no-verdict output.
All execution changes must precede root freeze and Claude approval.

## Prior evidence and predictions

Item 35 recorded bounds -27,266/-28,259 and 86/86 infeasible rounded proposals
across R/naming. Its final selected multiplicity in bins 9/10 is zero in both
cohorts, with 256 positive-weight selected entries and no ambiguous cutoff.
This supports testing coverage repair, not a causal claim about long bins.
The original predictions remain: warm preserves full coverage and seed F or
fails explicitly; cold may fail to find coverage within the same budget; no
nonpositive F witness is predicted. Both warm and cold outcomes are retained.

## Verification and launch boundary

Ten focused synthetic tests passed: exhaustive tiny dictionary/path optima,
matched warm/cold solves, negative-cost DAG behavior, optional-character
coverage, all incumbent rows/objectives, construction limits, zero-time warm
starts, deterministic verified pool extraction, two invented 300-program
report bundles with corruption/failure checks, and parent-enforced worker
termination. These establish implementation checks, not corpus qualification.

Root owns approval, launch, and recording. After review, the frozen executable
is `supervise.py --work <authorized-work-root> --output <fresh-private-run>`
under the pinned Python, with `OMP_NUM_THREADS=OPENBLAS_NUM_THREADS=MKL_NUM_THREADS=1`.
After completion, `report.py --run <same-private-run> --work <authorized-work-root>`
replays evidence independently. No retries, resume, or post-result pool edits
are authorized. The inherited exact qualification receipt is item 13; no new
source execution occurs. No private artifact is copied into the repository.

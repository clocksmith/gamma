# 44: Direct fraction exchange, proposed inactive freeze

2026-10-23. Prepared implementation; **not activated**. Root and Claude review,
then exact-match activation of the public-only pending contract, are required
before any private input is opened. The original pinned synthetic mechanism,
tests, benchmark and receipts remain byte-identical. Production time checks and
decoder charging are added in `search.CheckedGraph`, without changing them.

## Scope and inherited evidence

Run separate original-R and naming fixed-300-fit cohorts using exactly item 40's
ordered pool and measured seed. Rebuild the pool through the frozen item 35
certificate and item 40 extraction procedure, then compare its content/hash,
counts and occurrence graph with the recorded item 40 artifacts. Hash-bind the
parent private result and seed/warm/cold dictionaries through public item 40
metadata. Verify the original item 13 source qualification hashes; claim no new
source execution or repaired item 23 qualification.

Capacity 256 includes every singleton, with no implicit fallback. Inherit exact
whole-source and solve-definition/body bans. Retain item 40's construction caps:
2048 candidate entries, 2 million pool characters, 20 million trie transitions,
1 million occurrence arcs. Any mismatch or limit violation fails; no pruning,
pool enlargement, source change, or retry is allowed. Both observed seeds have
249 entries; verify that fact and seven free slots at execution.

No validation, held-out or protected input, source execution, description work,
training, block search, or new representation is included. One-owner and
near-whole words remain semantic-reuse relaxation witnesses, not M1 candidates.
Nearest-rank selection quantiles count N excluding Finish; actions=N+1. F=10C-N
tests the threshold C/N<=10%, but lower F need not reduce C/N or selections.

## Fixed algorithm and opportunity set

Use exact minimum-F paths, ties by minimum N then lexical entry sequence.
Verify original reference identities first, then sort literals consistently for
seed, warm, cold and direct packets. Preserve original dictionary hashes and
identify sorted reserialization separately. Cache word strings, never mutable
subset IDs. Adding words invalidates their occurrence owners; removing words
invalidates sources using them in the current canonical path. Recompute the
union for swaps; do not reject a swap merely because removal alone is uncovered.

Maintain a covering incumbent and accept only strict lexicographic improvement
in `(F,total N,full package including decoder sources)`. Exact sorted word order
breaks proposal ties but cannot alone justify acceptance. Fixed eight-bit packet
costs apply even below 256 entries. Temporary 257-entry addition scores are
ranking-only relaxations: their package value is algebraic, no such packet is
serialized, and the state cannot be retained or reported as a feasible witness.

Phase A: up to seven complete best-addition sweeps, stopping early if no improving
eligible addition exists. At each sweep score all currently inactive pool words.
Phase B: at most twelve epochs. Score all inactive words as additions (ranking
only if already at 256); score all selected words as removals; shortlist the four
best added words by exact addition objective then stable sorted pool ID; score
every selected removal jointly with each shortlisted addition. Choose the best
eligible neighbor across those three stages. No two-entry block moves run.

Every new best eligible proposal receives a full graph rescore before it can
become the best retained neighbor. Rescores count against the same search
budget as additions, ranking probes, removals, swaps and coverage failures.
No source-plan cache is retained for historical dictionaries: keep only the
current state, trial and best neighbor, plus scalar proposal scores. Checkpoints
store sorted dictionaries and scalar identity; packets are built after search.

Search budget per cohort: 600 seconds, 50000 attempted evaluations including
rescores, Phase A's verified free-slot limit, and twelve Phase B epochs. Check the
search clock before each evaluation and before/after each per-source DP. No new
probe or source recomputation starts after the search deadline. An interrupted
probe counts as attempted, not completed. Once the budget is reached, only
retention of an already fully evaluated/rescored best neighbor and final
bookkeeping continue under the whole-job guard. No incomplete trial is retained.
The measured search elapsed includes trace/checkpoint bookkeeping; any deadline
crossing and unfinished sweep remain explicit, rather than being described as
a completed search neighborhood.

An already checked best from a partial sweep may be the final incumbent. Record
its original evaluation and rescore IDs, and mark partial-sweep selection.
Completed opportunities and omitted opportunities are separate. Even a fully
completed no-improvement epoch is reported only as no improving evaluated
neighbor; no full-pool, global, or mathematical local-optimality claim follows.

## Resource and failure controls

R uses core 6; naming uses core 7. Each worker and supervisor has an 8 GiB address
space limit. One numerical thread; OMP/OPENBLAS/MKL all 1. Install affinity,
memory and whole-job alarms before input, pool or graph setup. A fixed alarm
is already armed before contract reads and filesystem preflight. Hard deadline
exceptions inherit directly from BaseException so ordinary exception recovery
cannot swallow them; final handlers preserve failure/no-verdict receipts and
disable the alarm before bounded process-group cleanup. The production
supervisor enforces 1200 seconds for the entire job, including all preflight,
pool reconstruction, search, independent final min-F verification, reference
and retained-incumbent packet writing, and collection. Independent reporting
receives a separate 1200-second cap on the same two cores. Process groups are
killed on worker failure or timeout; cleanup is separately recorded with a
maximum 10-second tolerance. No automatic retry or budget enlargement.

Seed cache construction is setup. Final independent min-F rescoring and packet
verification are separately measured verification costs under the whole-job
cap, not additional move proposals. The 600-second search opportunity budget
includes all in-search acceptance rescoring. The latter cannot silently be
moved into uncharged verification work.

Any full-job timeout, uncovered seed, lost incumbent, failed decode, input drift,
or independent reporter failure leaves retained failure receipts and no accepted
overall result. Seed retention is intentional from initialization, not a
substituted fallback. Each phase requires a fresh output directory. A refused
report rerun into an existing directory archives its old summary/report and
writes an explicit incomplete/no-verdict summary.

## Independent report and metadata

Reconstruct source, exact pool, original references, bans and parent evidence
independently. Independently decode and minimum-F rescore every reference and
retained dictionary, including the seed and final pointer. Recheck capacity,
full coverage, sorted ID order, F/C/N, packet framing/Finish, dictionary and
decoder bytes. Verify trace order, declared opportunities, exact probe IDs and
enumeration, attempted/completed counters, coverage-failure source witnesses,
acceptance/rescore links and strict monotonicity. Rejected proposal objectives
are search diagnostics, not independently certified optima.

The reporter exports only metadata/hashes and fixed enums. No source, pool
string, dictionary key, q, plan, packet, or arbitrary exception text is public.
Report seed/warm/cold/direct F,C,N,C/N, actions, median/p90/p95 selections,
dictionary/packet/decoder package costs, one-owner share, near-whole share and
their overlap. Near-whole is length>=90% of any containing source; all entries,
including unused entries and singletons, remain in share denominators. The
statistics describe support and size, not reuse legality. Retain both observed
coverage failures on interrupted probes and completed-failure counts distinctly.

The original parent full-substring lower bounds remain separately labeled.
Neither a better witness nor an unsuccessful bounded search changes those
bounds, proves solver optimality, or implies M1 or larger-population acceptance.

## Falsifiable predictions

1. Both cohorts finish with full coverage and no worse F than their seed
   (expected true; failed jobs remain failures).
2. The direct final F is strictly below item 40 seed/warm F in both cohorts
   (expected true).
3. At least one retained direct witness reaches F<=0 (expected false).

No directional prediction is registered for C/N, N or selection quantiles;
report their signed changes explicitly. Prediction outcomes require complete
independent replay, and are null on an incomplete overall result.

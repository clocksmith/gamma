# Static guard filtering improves bounded composition

On the ten original consumed fit captures, structural control returns 4/10
correct, the preserved recipe/literal route 7/10, and the new opt-in static filter
**8/10**. All arms have zero wrong acceptances and infrastructure failures, with
no lost correct answers. The added correct answer is lcd:2144 (candy discount).
All ten graphs remain valid; two semantic failures remain.

The original model selected a zero payment cutoff, so edits confined to the cycle
length could not make its payment branch execute. The new general proposal
heuristic derives conservative lower bounds for top-level integer variables only
when every write is a literal reset or nonnegative self increment. Unknown writes
invalidate the bound. It tracks sequential increments, branch merges and possibly
empty loops. A candidate with a provably unreachable nonempty numeric then-branch
is skipped before public execution. Graphs are strictly type-validated first.

This is a search heuristic, not a proof that every program containing dead code
is wrong. Accepted controls are preserved, unknown bounds cause no rejection,
and no query-specific values, expected output or target labels enter the filter.
The same model-logit order, eight-bit pool, at most two flips, four total extra
public executions and 0.25-second shared recipe/literal budget remain in force.
Default routes are unchanged. Rejected proposals retain explicit filter traces.
The candidate still uses 17 extra public executions across the ten cases.

All thirty public decisions were sealed before original hash-bound independent
source tests were loaded. The run completed in 4.464 seconds under two CPU
threads, 2 GiB and a 120-second cap. Capture replay excludes inference; this is
consumed-fit correctness evidence, not latency, release or generalization
qualification. Historical results and the two-second end-to-end gate are intact.

Six new focused tests passed, including negative/unknown writes, zero-iteration
loops and skipped-execution accounting; the existing 48 repair/judge/lane tests
also passed. The first combined invocation additionally collected five duplicate
imported fixture tests; those were removed from collection, not counted as new
coverage. Changed Python compiles and imports. No training, protected access,
worker intervention or downloads occurred.

The previous fresh 5/10 vs capture-only 7/10 losses are separate from the three
semantic failures: lcd:1051 has identical independently correct source but its
embedding took 3.466 seconds; lcd:1046 embedding took 2.436 seconds and exhausted
the gate before a valid construction/repair could be returned. The remaining
semantic cases after this change are lcd:1101 (three literal-bit differences)
and lcd:1489 (seven literal-bit differences); their established ranking/binding
problems are not repaired by this filter. No edit-count budget was expanded.

Evidence: [manifest](candidate.json), [summary](summary.json),
[seal](decisions-seal.json), [driver](run_guard.py). Full graphs, raw traces and
scores remain local under `runs/typed-guard-fit-128-v1`.

# Item 40: coverage-preserving fraction repair

Status: execution design prepared for root and Claude prelaunch review. Input
hashes are bound from the public item 35 record `a0f43fc3b`; no private source,
q or result file has been opened during preparation. This directory does not
authorize launch.

This asks whether a bounded dictionary pool can produce a covering witness with
`F = 10 C - N <= 0`, where C counts singleton selections and N counts all
selections. The two eventual populations are the original fixed 300-program R
and naming fit cohorts from items 33/35. No validation population is loaded.
Every singleton entry consumes a dictionary slot. There is no implicit alphabet.

The pool contains item 35's measured seed witness dictionary (with unused,
nonoccurring entries already removed and recorded there), the union of the shortest-depth
and longest-depth realizations of item 35's final-q top-256 selection, and words
used on its verified relaxed minimum-cost paths. Retain the seed and selected
tiers in full (at most 768 entries). Fill remaining slots, up to 2,048, with
path words ranked by decreasing `path_use_count * (9 * length + 1)` for words
longer than one character (zero for singletons), decreasing
distinct path-owner count, increasing length, then lexicographic string. This
ranking measures saved singleton cost for proposal allocation; the solver uses
exact F, not this heuristic. Deduplicate exact strings before ranking. Record
candidate provenance, proposed/admitted counts, omissions and all tie rules.
Every retained seed entry must occur in the fixed population; no legacy extras
are added outside the full substring pool.

The exact complete-source/solve-body bans are inherited unchanged. Rebuild and
independently verify the item 35 index, q and certificate before extracting pool
words. A banned seed or missing seed coverage is a failed precondition, never
silently repaired. Both endpoint realizations and every selected relaxed path
word must already be allowed. One-owner strings and near-whole strings are
permitted in this relaxation, with length/support diagnostics. This is not an
M1 candidate and does not settle semantic reuse. A negative witness does not
repair item 23's failed M1 result. Failure of this bounded pool does not prove
failure of the full substring space.

For every word there is a binary activation y. For every exact occurrence there
is a continuous flow variable f in [0,1]. Source-position flow conservation
sends one unit from each program start to end. Add f <= y for every occurrence
and sum(y) <= 256, including singletons. Occurrence cost is 9 for singleton
words and -1 for longer words, so the objective is exactly F. All edges strictly
advance within one source; negative costs create no cycle or unbounded path.
For fixed integral y, any feasible unit flow decomposes into paths. Therefore
an exact minimum-F path costs no more than the solver flow. Conversely every
dictionary and its paths give a feasible model point. This proves equivalence
of the integer activation model and the bounded-pool dictionary optimum even
though occurrence flow is continuous.

The warm point activates the seed and uses its exact minimum-F paths, with
ties by total selections then entry-ID sequence. Check every variable bound,
activation integrality, flow/link/capacity row, and objective before calling
HiGHS. The cold solve uses exactly the same immutable model and solver options,
without setSolution. Reuse item 26's checked solver adapter without editing it.
Independently rebuild exact paths for every returned dictionary: require full
coverage, capacity, bans, exact concatenation, and F no greater than its reported
flow objective within 1e-6. A warm solver losing its incumbent is a failure;
never substitute a fallback and call it a successful solve. Report both arms,
including infeasible/time-limited outcomes, and comparisons to the seed.

Review allocation, pending root scheduling and freeze: one CPU per cohort,
one solver thread, 8 GiB per worker, R warm then cold and naming cold then warm,
with 600 seconds for each solve,
2,400 seconds total per cohort including index replay, pool construction,
matrix construction and exact replay. Parent supervisor must bound the whole
job and kill process groups. Two cohorts may run concurrently only after the
assigned cores are free (R core 14, naming core 15, subject to Claude availability).
An outer 2,500-second whole-job guard also covers both workers and all
preflight/collection work. The parent independently enforces each cohort's
2,400-second cap because Python alarms can be deferred inside a native solver.

Finite construction limits are 2,048 pool entries, 2,000,000 total
pool characters, 20,000,000 source/trie transitions and 1,000,000 occurrence
arcs. Breaches fail explicitly; no arc truncation. Trie construction costs
O(total pool characters), occurrence scanning O(transitions + arcs), matrix
storage O(source positions + pool entries + arcs). Source scanning can be
quadratic for adversarial long common prefixes, which is why its independent
transition cap and whole-process wall limit are required. Model matching is
deterministic by program ID, source position, and increasing endpoint.

Known prior evidence, recorded before this freeze: item 35's exact bounds were
-27,266 for R and -28,259 for naming. All 86 rounded proposals (42/44) failed
coverage. Its final top-256 selection has 256 positive-weight entries in each
cohort, zero selected multiplicity in bins 9/10 (lengths 129–256/257+), and no
ambiguous cutoff selection. Thus there is no observed long-bin selection
dominance to explain. Coverage-preserving repair tests a separate primal
construction issue; it does not attribute the dual's residual weakness to any
particular bin. These observed parent facts do not change the pool, ranking,
budget, or registered predictions.

Registered predictions: warm returns a full-coverage nonregressing witness or
fails explicitly; cold may spend its budget finding coverage. A nonpositive
F is not predicted. Optional characters may be removed only if the complete
population remains encodable. Report
the seed, warm and cold F/C/N, fraction, entries, dictionary/packet bytes,
per-program costs, entry length/support/near-whole diagnostics, exact source
qualification pins, solver bound/gap, resource outcomes, and private artifacts.
Public reporting contains numeric metadata and hashes only, never source,
dictionary strings, q, or packets.

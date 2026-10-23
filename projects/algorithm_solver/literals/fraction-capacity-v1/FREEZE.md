# Capacity-aware character-fraction certificate

Board25, goal2a diagnostic. Item21 minimized character fraction over paths for
fixed dictionaries, so it could not rule out another dictionary. Item8 bounded
selection counts over a declared pool, but did not address the10%character-bit
gate. Combine those questions with a capacity-aware bound on F=10C-N, where C is
single-character selections and N is total selections. Eight-bit selections make
C/N exactly the character-bit fraction. No candidate promotion is attempted.

## Sources, pools and scope

Use only item13 control256 R and scope_joint256 naming fit300 source files and
seed dictionaries. Never load validation source values, cases, final held-out100
or protected66. Metadata proof receipts contain previously consumed validation
counts but are used only for fit hash/qualification identity. No corpus costs,
pool counts or character probe preceded this freeze. Naming sources are a
previous adaptive development selection, not independently confirmed material.

For each cohort, build the shared pool of every2–64byte substring occurring in
at least two distinct fit programs, excluding all fit complete sources/solve
definitions/bodies. Union in every pinned seed learned entry, including any that
falls outside the newly mined pool; report that scope explicitly. This guarantees
the seed is a feasible primal upper bound. No other one-owner/long strings enter.
Pools, occurrence order, sources and seeds are privately pinned by hashes.

Two capacity models per cohort:

- fixed96: all96ASCII fallback characters mandatory, at most160pool strings;
- flex256: no mandatory entries, at most256entries from the same learned pool
  plus all96characters. Character entries participate in activation/capacity.

Flex256 relaxes item24's reserved-unseen-character policy. The learned pool here
is broader than each bounded repair proposal set, and the bound covers every
subset within its specified capacity. It does not cover arbitrary strings,
source changes, other corpora, arbitrary subsets of the300fit programs, quantile
gates or the frozen500 M1 population. A positive bound is a restricted-source/
pool impossibility certificate only; it does not kill the broader concept.

## Dual and exact certificate

For each source, build an acyclic occurrence graph. A character edge costs9;
a multi-character edge costs−1. Summing path edges yields10C−N. Negative edges
are safe in this forward-only DAG; there are no cycles or unbounded traversals.
Each optional occurrence o has a shared dictionary activation x_e and y_o<=x_e.
Relax these constraints with lambda_o>=0. Mandatory edges have no multiplier.

    L(lambda) = sum_p shortest_path_p(base_edge_cost + lambda_o)
                - sum of the B largest entry multiplier sums

Here B is160or256. Entry sums are nonnegative, so topB solves the at-most-B
activation subproblem, including harmless zero sums. Weak duality gives a lower
bound on F for every feasible dictionary AND every segmentation of all300sources.
Continuous occurrence flows do not weaken the per-fixed-dictionary shortest-path
argument: integral shortest paths exist on the DAG.

Quantize the best floating-point multiplier vector to q=floor(lambda*1,000,000).
Any resulting nonnegative integer q is a valid dual point. Recompute shortest
paths and topB entry sums with Python integers, storing numerator/denominator and
ceil(numerator/denominator). A separate forward-DAG verifier re-enumerates source
substrings/occurrence order independently and recomputes the exact numerator.
It must agree. Store q and pool privately with hashes; no float solver bound
alone is called a certificate.

If the integer lower bound is positive, EVERY covered300-program representation
in that exact model has10C-N>=1 and therefore C/N>10%. If nonpositive, the bound
is inconclusive unless a separately decoded feasible witness has F<=0. Such a
witness demonstrates reachability only for its complete fit cohort/model; it is
not proof of minimal ratio. MinF and minC/N are different optimizations. Report
witness N,C,actions,quantiles,coverage and storage, even if fractional savings
come from more selections.

## Bounded multiplier search and witnesses

Start all multipliers at0. Polyak subgradient ascent uses a feasible upper bound,
initially the seed's exact minimumF encoding. Step theta starts1, halved after
30iterations without a real-bound improvement. Update nonnegative multipliers
using y_o-x_e and theta*(upper-current_bound)/squared_gradient_norm. Keep the best
real-bound vector only for subsequent exact certification.

Every25iterations, try up tothree primal dictionaries ranked by entry multiplier
sums, current relaxed usage and exponential usage average (0.9old+0.1new). Ties
use pool order; select at mostBpositive-ranked candidates plus mandatory entries.
A flex proposal lacking coverage is discarded as infeasible, never assigned a
partial cost or repaired. All feasible proposals use exact minimumF paths, then
minimumN, then lexicographically first IDs. Keep best generated separately from
the seed/incumbent; it may be absent when no proposal covers allfit sources.
No local polish, changed sources, extra unbudgeted refinement or validation.

At most2000iterations or1200seconds per model, measured from after graph
construction. Pool/graph construction and final replay are included in total arm
and run wall time. A final iteration can cross its guard. Stop earlier at zero
gradient or real upper-minus-bound<1; exact certificate remains the authority,
not that floating stopping condition. Four models on cores8–11, one process/core,
OMP/BLAS1,8GiBaddress-space per process,2400-second overall cap. Item24 uses0–7;
Claude22 uses26–31. Pinned Python3.14.4/NumPy2.4.4; no installation/GPU/model.

Every iteration appends a private live numeric receipt before continuing. Final
seed, best and generated (if available) witnesses each encode/decode all300fit
sources through the canonical literal codec. The minimumF path may differ from
canonical minimumN encoding; the decoder and stored literals are unchanged. All
entries, selections, Finish,41-byte frames and dictionary bytes count. Report
per-program/amortized package and decoder-source inventory separately; the full
installed runtime footprint is unmeasured. No source/case execution is claimed;
item13 qualification is reused by exact fit source hash. Item23's later retained
exit137 failure on an unchanged naming source is not revised by this diagnostic.

## Predictions and reporting

- B1: all four exact certificates pass the independent forward replay and are
  no higher than their decoded best feasible witness objective.
- B2: the fixed96 certificate is positive in both cohorts.
- B3: the flex256 certificate is nonpositive in both cohorts (capacity relaxation
  may leave the current dual inconclusive).
- B4: no generated feasible witness reaches F<=0 in either capacity model.
- B5: at least one model's generated feasible witness improvesF over its seed.
- B6: all final available witness packets decode, with clean fit body audits.

Report every sign/gap, model/pool scope, stop/time, optional proposal failure count, witness costs and prediction.
No readiness, selected successor, global impossibility, universal optimality or
M1 conclusion. Positive B2 alone does not establish that a learned scorer cannot
help other objectives or that source rewriting is exhausted. Any future search
change needs its own freeze; no gates or claims are inferred from this run.

Five synthetic tests pass: negative-edge/tie/coverage semantics;60tiny mixed
mandatory/optional dictionary problems with exhaustive feasible dictionary
objectives and random dual points;60exhaustive segmentation checks; exact positive
certificate/nonpositive witness examples; and optional-character optimizer/replay.
Compile/import/help and all code/runtime/input identity hashes precede launch.
Freeze/code/contract pushed, then Claude review or PLAN30-minute timeout before
measurement. Reports remain separately rerunnable without multiplier search.

Component intent and production boundaries preserved. No ledger/catalog/claim
writes, training, protected opening, source/codebook publication, BITS deployment,
independent confirmation or human study. Those owner gates remain unchanged.

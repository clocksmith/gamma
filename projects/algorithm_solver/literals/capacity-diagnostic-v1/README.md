# Phase 3 Tri-State Capacity Diagnostic, Connected Theorem A Search & Theorem B Parse Test (`capacity-diagnostic-v1`)

Pure Python stdlib, no LP/MILP solver. Frozen runs in `sixbit-v1/`, `capacity-impossibility-v1/`, `witness-coverage-v1/`, and `capacity-theorems-v1/` are untouched.

## 1. Reproducible First Deliverable

```sh
cd projects/algorithm_solver/literals/capacity-diagnostic-v1
python3 -B diagnostic.py --controls
python3 -B -m unittest discover -v
python3 -B connected_search.py
shasum -a 256 -c SHA256SUMS
```

## 2. What `diagnostic.py` Implements

- **Character-cooccurrence component decomposition (full-corpus capacity):** splits programs into connected components, computes mandatory-block rank (checked under two independent primes `(1_000_000_007, 2)` and `(998_244_353, 3)`) and a verified disjoint-position witness per component, and sums `max(rank_lb, disjoint_lb)` across components. On the 7-program union `["abd", "abe", "fbd", "pxqy", "qypx", "pyqx", "qxpy"]` under `W2`, this returns **`9`** (`5 + 4`, not `8`), certifying `K = 8` `IMPOSSIBLE` and `K = 9` `FEASIBLE`.
- **Strict tri-state verdict:**
  - `IMPOSSIBLE` — certified lower bound exceeds budget `K` (or an unspellable position exists), with per-component certificates.
  - `FEASIBLE` — **only** when an eligible dictionary of size `<= K` is constructed and independently verified to reconstruct every source byte-for-byte. A rank bound is never reported as a construction.
  - `UNRESOLVED` — certified `[LB, UB]` interval when neither impossibility nor a verified construction is established.
- **Threshold-monotonicity saturation reuse:** attaches `monotoneSaturation` (`reusableForAllThresholdsAtLeast = k`) **only** when `k >= 2`, `certifiedLowerBound == |Sigma|`, and all singletons in $\Sigma$ remain eligible.
- **Separate partial-coverage allocation:** `allocate_partial_coverage(component_curves, shared_budget)` allocates a shared slot budget across components via exact knapsack DP (never adding per-component coverage as though each component received the full budget).
- **Measured runtime and memory:** every verdict records `elapsedMs` and `peakAllocKiB` (`tracemalloc`). No unproven asymptotic complexity is claimed.

## 3. Connected-Component Search for Theorem A (`connected_search.py`)

- **Pre-registered Round 1 (`PREREGISTRATION-CONNECTED.md`, 60 connected corpora across Families B1/B2/B3):** **`0/60` hits** (`connected-results.json`). Every B1/B2/B3 bridge injected a forced singleton into $M_2$, breaking $M_2$'s rank-3 invariant and lifting `blockRank` to $|\Sigma|$.
- **Post-Round-1 reasoned counterexample (`counterexample-connected-after-round1.json`, clearly separated from frozen Round 1):**
  - Prepending shared block `"ab"` from $M_1$ onto `"pxqy"` in $M_2$ connects the program character-cooccurrence graph across a forced cut (`b|p`) without injecting any singleton into $M_2$.
  - Minimized counterexample: **`["abd", "fbd", "abpxqy", "qypx", "pyqx", "qxpy"]`** (6 programs, $|\Sigma| = 8$, **1 program-connected component**, all singletons eligible): **`blockRank = 7 < 8`** (both primes), exact **`disjointBound = 7 < 8`**, exact exhaustive **`OPT_W2 = 8 == |Sigma|`**.
  - **Structural takeaway:** while program-connected, its *forced blocks* still split into 2 disconnected components (`{ab, abd, bd, f}` with `blockRank = 4` and `{px, py, qx, qy}` with `disjointBound = 4`, sum `8 == OPT`), sharpening the next open test for Theorem A to a single **forced-block connected component**.

## 4. Theorem B Parsing Test (`theorem_b_span_parse_test`)

Tests directly whether candidate basis tokens admit a complete contiguous non-overlapping parse for every source under rule `U`:
- **Lemma (Span-Token Restriction):** any legal size-$r$ dictionary ($r = \text{rank}(M_\mathcal{T})$) must draw all tokens from $E_{\text{span}} = \{t \in \mathcal{E}_U(\mathcal{T}) : v(t) \in \text{span}(M_\mathcal{T})\}$ as a linearly independent basis that parses every source.
- **Negative controls verified:**
  - `["ax", "ay", "bx", "by"]` (`rank = 3`): $E_{\text{span}} = \emptyset$ -> fails complete parse-in-span immediately (`LB = 4`).
  - `["axby", "byax", "aybx", "bxay"]` (`rank = 3`): passes cuttable-prefix and complete parse-in-$E_{\text{span}}$, yet fails size-3 basis-parse attainability (`LB = 4`).
- **Positive control verified:** `["abc", "abab"]` (`rank = 2`) attains rank with byte-verified dictionary `["ab", "c"]`.

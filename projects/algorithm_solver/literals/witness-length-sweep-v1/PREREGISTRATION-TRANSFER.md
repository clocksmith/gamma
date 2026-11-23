# Pre-Registration: Unseen-Program `K x L` Transfer Test (`witness-length-sweep-v1`)

**Status:** Frozen before execution. Do not modify this file, `run_unseen_transfer.py`, or `check_unseen_transfer.py` after recording `SHA256SUMS-TRANSFER-FROZEN`.

## 1. Research Question

When a dictionary of `K` entries with maximum entry length `L` is trained and **frozen** on one cohort (`-a`) and evaluated without modification on a **disjoint unseen cohort (`-b`)** from the same source family, do jointly chosen `W(L)` multi-character fragments yield a repeatable unseen-program coverage advantage over single-character selection (`L = 1`) or frequency-picked baselines at matched slot budget `K` (and at what stored dictionary byte cost)?

## 2. Frozen Inputs and Experimental Arms

Source inputs are read directly from the already-frozen disjoint `-a` / `-b` cohorts in `../witness-scaling-v1/cohorts.json`:
- `J-80-a -> J-80-b` (`80` train, `80` unseen holdout; lodash JS)
- `P-80-a -> P-80-b` (`80` train, `80` unseen holdout; CPython stdlib)
- `J-160-a -> J-160-b` (`160` train, `160` unseen holdout; lodash JS)
- `P-160-a -> P-160-b` (`160` train, `160` unseen holdout; CPython stdlib)

Across `L in {1, 2, 4, 8, 16, 32, 160}` and every slot budget `K in 0..|Sigma_a|`, each arm trains **exclusively on `-a`**, freezes its dictionary (every entry checked for strict `W(L)`-legality on `-a`), records exact stored dictionary bytes (`sum(len(w))`), and replays byte-for-byte on both `-a` (train) and `-b` (unseen holdout):
1. **Arm (a) Character selection (`L = 1`):**
   - `charOpt`: exact single-character MILP optimum on `-a` (replayed on `-a` and `-b`).
   - `charFreqDoc`: top-`K` single characters ranked by `(doc_freq DESC, total_occ DESC, bytes ASC)` on `-a`.
2. **Arm (b) Frequency-picked `W(L)` substrings on `-a`:**
   - `freqOcc`: top-`K` `W(L)`-legal entries on `-a` by `(total_occ DESC, doc_freq DESC, len ASC, bytes ASC)`.
   - `freqDoc`: top-`K` `W(L)`-legal entries on `-a` by `(doc_freq DESC, total_occ DESC, len DESC, bytes ASC)`.
3. **Arm (c) Jointly chosen `W(L)` reusable fragments on `-a`:**
   - `jointBest`: best `-a`-verified `W(L)`-legal dictionary across `charOpt`, 4-start greedy shortest-path DP capped at `L`, rare-character cluster compression capped at `L`, and inherited `L' < L` dictionaries, selected strictly by highest `-a` train coverage (tie-breaking on `-a` by fewest entries, then smallest stored dictionary bytes).
   - `greedyDP`: best pure multi-start greedy shortest-path DP dictionary capped at `L` on `-a` (without falling back to `charOpt`), measuring how fragment-heavy dictionaries transfer to unseen `-b` programs.

For every `(pair, L, K)` where `jointBest` or `greedyDP` spells strictly more unseen `-b` programs than `charOpt`, the script records the exact gained `-b` program IDs and the actual multi-character fragments used in parsing them.

## 3. Falsifiable Predictions (T1 to T3)

| Id | Prediction | Pass Criterion |
| --- | --- | --- |
| **T1** | **No repeatable unseen-program fragment advantage for `jointBest` over `charOpt`.** | At `L = 160`: peak unseen `-b` lift `max_K (jointBest - charOpt) <= 2` on `>= 3/4` pairs; unseen lift at `K = 64` is `<= 0` on `>= 3/4` pairs; and `abs(mean_K(jointBest_test - charOpt_test)) < 1.0` program on all `4/4` pairs. |
| **T2** | **Pure fragment-heavy `greedyDP` loses to `charOpt` on unseen `-b` while costing more dictionary bytes.** | At `L = 160`: `mean_K(greedyDP_test) < mean_K(charOpt_test)` on all `4/4` pairs, AND `dictBytes(greedyDP, K=64) > dictBytes(charOpt, K=64)` on all `4/4` pairs. |
| **T3** | **Raw frequency-picked `W(L)` substrings collapse on unseen `-b`, while `charFreqDoc` tracks `charOpt`.** | For every `L >= 4` and all `4/4` pairs at `K = 64`, `freqOcc_test <= 1` and `freqDoc_test <= 1`; `charFreqDoc_test(64) >= 0.80 * charOpt_test(64)` on `>= 3/4` pairs; and `check_unseen_transfer.py` verifies 100% of frozen dictionaries solver-free. |
| **T4** | **Explicit promotion bar for a vocabulary-design claim ("substantially more unseen programs").** | At matched slot budget `K` (any `K in 0..|Sigma_a|`, evaluated at `L = 160` and across all `L >= 2`) AND at matched stored dictionary byte budget `B` (`dictBytes <= B`), jointly chosen reusable fragments (`jointBest` or `greedyDP`) must spell `>= +5 percentage points` of unseen `-b` programs (`>= +4` of `80`, `>= +8` of `160`) above the stronger of `{charOpt, charFreqDoc, freqOcc, freqDoc}` on at least `2` of the `4` held-out pairs (`J-80, P-80, J-160, P-160`). Failing T4 triggers reporting a null/negative transfer result and framing the manuscript strictly as a certificate/boundary study rather than a vocabulary-design breakthrough. |

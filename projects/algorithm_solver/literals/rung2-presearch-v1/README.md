# BITS Rung 2 Pre-Search Predictor & Equal-Budget Oracle (`rung2-presearch-v1`)

Implements the Rung 2 pre-search rule and equal-budget evaluation harness for BITS, kept
strictly separate from the frozen `dcc-v5` preprint bundle (`../codenet-replication-v1/`).

## Scientific Question (Rung 2)

Before running any dictionary search (`engine.c`) or shortest-path/Huffman parsing
(`byte_encode.py`), can a cheap $O(N)$ rule seeing **only raw corpus byte statistics**
pick both the archive layout (`A`: shared dict + 1 table, `B`: shared dict + 2 tables,
`C`: 2 separate dicts + 2 tables) and slot budget `K_hat`, saving search time while
keeping byte regret small against an equal-budget oracle?

## Frozen Pre-Search Rule (`raw_predictor.py`)

`predict_presearch(docs_1, docs_2)` computes only raw byte, alphabet, and stride-1 4-byte
window statistics (calibration frozen solely on `codenet-replication-v1` Python/JS ranks
`0..399`):

1. **Exact pre-search feasibility cliffs:**
   - Shared Designs `A` and `B` require $K \ge |\Sigma_1 \cup \Sigma_2|$.
   - Separate Design `C` requires $K \ge |\Sigma_1| + |\Sigma_2|$.
2. **What the rule adds beyond textbook single-byte mutual information ($I_1(X; L)/8$):**
   - **Multi-scale lexical divergence without singleton bias:** Two programming languages
     sharing ASCII character frequencies can have tiny single-byte mutual information
     (`i_byte`) while diverging strongly on multi-byte keywords. Filtering stride-1 4-byte
     windows to total support $\ge 6$ (`supported_gram4_mi_bits`) removes Miller-Madow
     singleton finite-sample KL bias from 1-occurrence identifiers that never enter $D$.
     `predict_naive_byte_mi` provides the direct single-byte MI ablation.
   - **Exact Design B vs. Design C header identity:**
     $$H_C - H_B = \sum_{w \in D_{\cap}} (3 + |w|) - (|D_1| + |D_2|)$$
     Every shared single byte saves $4\text{ B}$ in Design B and every shared $\approx 4$-byte
     token saves $\approx 7\text{ B}$, whereas every unshared language-specific entry adds
     $+1\text{ B}$ of zero-count table overhead in the other language's Huffman table. When
     alphabets and recurring substrings are disjoint ($\Sigma_1 \cap \Sigma_2 = \emptyset$),
     $H_C - H_B < 0$ and Design C wins.
   - **Pre-search slot budget selection (`K_hat`):** Estimates active amortized dictionary
     size from recurring 4-byte support (`rep12`) and picks the smallest $K \in \mathcal{K}$
     with $\ge 15\%$ prefix-selection headroom, avoiding wasted search at $K = 4{,}096$ on
     smaller corpora.

## Equal-Budget Oracle (`equal_budget_eval.py`)

Fixes both evaluation asymmetries from `codenet-replication-v1/run_replication.py`:

1. **Zero cross-layout union floor (`allow_union_floor = False`):** Shared layouts `A` and
   `B` never receive union dictionaries synthesized from Design C's per-language chains, and
   executing `(layout_hat, K_hat)` never runs unused layouts.
2. **Equal wall-clock search cap & exhaustive Pareto reparsing for Design C:** Shared search
   (`both`) receives `limit_seconds` total (`limit_seconds / |arms|` per arm), and Design C
   receives `limit_seconds / 2` on language 1 plus `limit_seconds / 2` on language 2
   (`total == limit_seconds`). Every Pareto-undominated prefix of each language is scored
   under iterative bit-cost reparsing (`optimize_byte_segmentation`) and **all** feasible
   $(K_1, K_2)$ pairs ($K_1 + K_2 \le K$) are evaluated without a 7-pair shortlist.

All candidate language pairs outside `codenet-replication-v1` are treated strictly as
empirical hypotheses (`hypothesis_status: "empirical_evaluation"`), never assumed winners.

## Verification

```bash
/usr/bin/python3 -m py_compile raw_predictor.py equal_budget_eval.py test_rung2_presearch.py
/usr/bin/python3 -B test_rung2_presearch.py
```

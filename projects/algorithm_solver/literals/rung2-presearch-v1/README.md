# BITS Rung 2 Pre-Search Predictor & Equal-Budget Oracle (`rung2-presearch-v1`)

Implements the upgraded Rung 2 pre-search rule, saved-data audit, and decoupled equal-budget
evaluation harness for BITS, kept strictly separate from the `dcc-v5` preprint bundle
(`../codenet-replication-v1/`).

## Upgraded Rung 2 Bar & Prior-Art Boundaries

1. **Why "2x faster within 1%" was too weak:** On CodeNet at $K = 4{,}096$, shared strings with
   separate per-language Huffman tables (`Design B`) beat separate dictionaries (`Design C`) by
   only `642 B` (`0.8%`) and `815 B` (`0.9%`), below the frozen `1.0%` materiality bar. A
   trivial policy that always runs `Design B` gets an automatic `2x` search speedup by skipping
   `Design C` while passing `< 1%` on those cells without learning anything.
   - **Upgraded layout bar:** First verify that fair-search cells exist where `default_always_B`
     (with two-part MDL byte-cost stopping) loses to the equal-budget oracle by **`> 1.0%`**,
     then test whether the frozen predictor beats `default_always_B` on those `> 1.0%` misses
     without regressing elsewhere.
2. **Why layout and stopping size must be scored separately:** Selecting the `1,600`-entry
   prefix over the `4,096`-entry endpoint along one greedy/BPE chain is ordinary two-part MDL
   amortization ([Liyanage & Yvon, 2026](https://arxiv.org/abs/2610.26225);
   [Nouri, 2026](https://arxiv.org/abs/2609.31705)), and greedy off-line phrase selection by
   net archive-bit contraction $G(w) = f_w B m_w - (B m_w + l(m_w) + l(f_w) + f_w l_{\text{ptr}})$
   is classical ([Apostolico & Lonardi, *Proc. IEEE* 88(11):1733–1744, 2000](https://doi.org/10.1109/5.892709)).
   `equal_budget_eval.py` therefore scores **layout choice** (holding MDL byte-cost stopping
   fixed at $K_{\max}$) and **pre-search `K_hat` stopping truncation** (holding layout fixed
   against `mdl_byte_stop_kmax` and `token_min_fill_kmax`) as separate additive terms.

## Saved-Data Audit (`audit_saved_codenet.py` -> `results/saved_codenet_audit.json`, $0 compute)

From `../codenet-replication-v1/results/codenet_results.json`:

- **Slot-budget penalty jump (`s1-whole`, $L=16$, reparsed Design A):** `0.66%` / `0.67%` at
  $K = 256$, **`0.00%` / `0.00%` at $K = 512$ and $K = 1{,}024$**, `1.19%` / `1.01%` at
  $K = 2{,}048$ (just past the `1,600`- and `1,552`-entry optima), and **`18.17%` / `17.17%` at
  $K = 4{,}096$**.
- **Small-sample plug-in MI drift:** Plug-in $I_{\text{tok}}(S; L)$ inflates **`1.96x`** from
  `0.3384` bits/token at `200` pairs to `0.6631` bits/token at `5` pairs due to Miller-Madow
  finite-sample positive bias, causing uncorrected plug-in rules to call break-even ~2x too
  early.
- **Miller-Madow debiasing (`raw_predictor.py`, `bits-rung2-presearch-v2`):** Subtracts exact
  first-order $2 \times |A|$ contingency bias $\frac{|A_{\text{obs}}| - 1}{2 \ln 2}$ on single
  bytes and stride-adjusted $4 \cdot \frac{|\mathcal{G}_{\ge 6}| - 1}{2 \ln 2}$ on supported
  4-byte windows before comparing against $|D| + 5$, alongside the exact Design B vs. Design C
  header identity $H_C - H_B = \sum_{w \in D_{\cap}} (3 + |w|) - (|D_1| + |D_2|)$.

## Untouched Holdout Evaluation (`run_untouched_holdout.py` -> `results/untouched_holdout_v2.json`)

Evaluated on 12 untouched first-party workspace cells (`Zig vs WGSL`, `C vs TypeScript`,
`Shell vs WGSL`, and disjoint `Zig vs Zig` negative control at $n \in \{8, 30, 75/80\}$) with
`raw_predictor.py` frozen prior to execution (`gamma@788807973`):

- **Small / homogeneous regime (`zig_vs_zig_ctrl_n8`, `zig_vs_zig_ctrl_n30`):** `default_always_B`
  (even with MDL stopping!) loses by **`+163 B (+1.38%)`** and **`+521 B (+1.46%)`** (`> 1.0%`),
  and the Miller-Madow-debiased predictor picks `(A, K=512)` and `(A, K=1024)` with **`0 B`
  regret** on both while uncorrected plug-in MI falsely picks `B`.
- **Cross-language mid-size regime (`zig_vs_wgsl_n30`):** Under fair equal-budget search,
  `Design C` beats `Design B` by `+147 B (+0.55%)` and the predictor hits `(C, K=1024)` exact
  (`0 B` regret). On `sh_vs_wgsl_n8`, `ora = C` beats `default_B` by `+164 B (+1.37%)`, where
  the predictor picked `B` (missing that small-corpus `C` win).
- **Tight wall-clock search regime (`2.5s` total = `0.5s`/arm on 260–300 kB `n=75/80` corpora):**
  Merged 300 kB `both` search hits `engine.c`'s per-arm time cap early (`stopped=1`), whereas
  splitting into two 150 kB per-language searches (`Design C`) completes deeper greedy chains.
  Re-running `zig_vs_zig_ctrl_n80` (`279,316 B`) with `limit_seconds=60.0` confirms the true
  completed-chain oracle winner is `(A, K=2048)` (`83,668 B` vs `default_B = 84,347 B`, matching
  `pred = (A, K=2048)` with `0 B` layout regret and `+679 B` layout gain over `default_B`, while
  ordinary MDL byte-cost stopping saves `11,948 B` over `4,096`-slot token-min filling).

## Verification

```bash
/usr/bin/python3 -m py_compile raw_predictor.py equal_budget_eval.py test_rung2_presearch.py audit_saved_codenet.py run_untouched_holdout.py
/usr/bin/python3 -B audit_saved_codenet.py
/usr/bin/python3 -B test_rung2_presearch.py
```

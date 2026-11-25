# BITS Rung 3: Variational Two-Part MM Subset Selection & Certified Nash Fixed Points (`rung3-vmm-subset-v1`)

Addresses two questions left open by fixed-dictionary iterative bit-cost reparsing (`byte_encode.py`)
and merge-order MDL prefix stopping ([Liyanage & Yvon, 2026](https://arxiv.org/abs/2610.26225);
[Nouri, 2026](https://arxiv.org/abs/2609.31705)), kept strictly separate from `../codenet-replication-v1/`
and `dcc-v5`:

1. **Certified Mutual (Nash) Fixed-Point Verifier (`certify_emitted_table_optimality`):**
   Checks whether an emitted `(parse, canonical Huffman table)` pair has **`0` bits of parse
   suboptimality** under its own active table `D_active = {w in D : lengths[w] > 0}` (eliminating
   provisional zero-count penalties), and proves monotone integer-bit convergence to a `0`-bit
   certified fixed point (`polish_to_certified_nash_single`).
2. **Variational Two-Part MM Subset Selection (`variational_two_part_mm`):**
   Minimizes `dict + Huffman table(s) + payload` over **arbitrary subsets** $D' \subseteq D_0$
   ($\Sigma \subseteq D'$) without requiring a merge order, using the tight additive per-occurrence
   surrogate weight $\tilde{c}_s^{(t)}(w) = \ell_s^{(t)}(w) + \frac{8(1 + |w| + n_{\text{tables}})}{n^{(t)}(w)}$
   for $w \notin \Sigma$, followed by exact $\gamma = 0$ Nash fixed-point polishing.

## Empirical Results (`results/vmm_subset_results_v1.json`)

### 1. Exported CodeNet Nash Certificate & Unordered `tokbest` Rescue Audit

- **`32/32` (`100%`, `max_parse_suboptimality_bits = 0`)** exported dictionary streams in
  `codenet-replication-v1/dictionaries/*.hex` are certified global shortest-path optima under their
  emitted active Huffman tables.
- **Unordered `K = 4,096` `tokbest` rescue (where prefix stopping is impossible):**
  - Deleting zero-count entries alone saves only `85 B` (`primary`: `101,108 -> 101,023 B`) and
    `191 B` (`secondary`: `103,392 -> 103,201 B`), proving the `18.2%` / `17.2%` penalty comes from
    positive-count unamortized entries rather than unused header slots.
  - **Variational Two-Part MM** collapses unordered `tokbest` to **`85,535 B`** (`1,952` entries,
    recovering **`100.16%`** of the `15,548 B` penalty on `primary`, edging `85,560 B` size-selected
    `A_tm` by `25 B`) and **`88,495 B`** (`1,997` entries, recovering **`98.30%`** on `secondary`).

### 2. Conditional Attribution vs. Two-Part MDL Prefix Stopping (`BIT3` Random Access)

| Suite & Seed Chain | `MDL-prefix-stop` In / Held-Out (`B`) | `VMM-subset` In / Held-Out (`B`) | `VMM` Gain In / Held-Out (`B`) | Attribution |
|---|---:|---:|---:|---|
| CodeNet `BPE-4096` | `93,058` / `103,200` | **`87,883` / `101,795`** | **`+5,175` / `+1,405`** | Excises absorbed BPE sub-merges; wins both |
| `short_wgsl_vs_json` `BPE-1024` | `11,345` / `12,071` | **`10,445` / `12,020`** | **`+900` / `+51`** | **New best `12,020 B` held-out on WGSL/JSON** |
| `short_ts_vs_mjs` `BPE-1024` | `12,721` / `13,387` | **`11,474` / `12,898`** | **`+1,247` / `+489`** | Wins both in-sample (`-9.8%`) & held-out (`-3.7%`) |
| CodeNet `greedy-byte-4096` | `89,119` / `101,355` | **`85,972` / `100,930`** | **`+3,147` / `+425`** | Prunes short-fragment bloat; wins both |
| CodeNet `greedy-entry-4096` | `86,075` / **`100,567`** | **`85,749`** / `103,564` | **`+326`** / `-2,997` | Admits `c=3..4` tail phrases -> held-out OOV |

- **Mechanism separation:** Bottom-up BPE traps dead intermediate scaffolds (`"re"`, `"ret"`,
  `"retur"`) near the front of its merge chain, so `VMM` beats `MDL-prefix-stop` on **all 3 suites
  both in-sample (`-5.6%` to `-9.8%`) and held-out** (setting a new `12,020 B` held-out mark on
  `short_wgsl_vs_json`). Conversely, top-down `greedy-entry` already avoids bottom-up scaffolds, so
  applying unregularized in-sample `VMM` across a deep `4,096` tail admits corpus-specific `count=3..4`
  strings that win `+326 B` in-sample while overfitting unseen files.

### 3. 2x2 Mechanism Ablation: Pooled-Substring Revival & Leave-One-Document-Out Transfer VMM (`transfer_vmm.py`, `results/transfer_vmm_2x2_results_v1.json`)

Diagnoses and resolves both structural limits of one-shot `Base VMM` (`revival=False, shrinkage='none'`):
1. **Superstring-Substring Nash Lock-In (`revival=True`):** Long low-count superstrings (`c=2`) steal
   occurrences from core substrings (`c -> 1`), inflating the substring's one-shot header surcharge so
   neither yields. Pooling active superstring counts & document bitmasks during de-cannibalization
   breaks lock-in (**`9/9` (`100%`) in-sample wins** vs. `MDL-prefix-stop`, `+13,220 B` net saved).
2. **Leave-One-Document-Out Risk Shrinkage (`shrinkage='loo_doc'`):** Weighting non-singleton headers
   by $df(w) / (df(w) - 1)$ (`+\infty` for $df \le 1$) eliminates single-document burst memorization:
   - **`TransferVMM` (`revival=True, shrinkage='loo_doc'`) wins `9/9` (`100%`) held-out single-chain
     cells (`+16,161 B` net saved vs. `MDL-prefix-stop`, `+17,864 B` vs. `Base VMM`) and beats both
     single-mechanism ablations on all `12/12` rows (including unordered `Union(BPE, greedy-entry)`)**:
     - CodeNet held-out `BIT3`: **`96,956 B`** (`greedy-entry`, `+3,611 B` vs. `MDL`, `-6,178 B` vs. `Base`), **`97,954 B`** (`greedy-byte`), **`98,294 B`** (`bpe`, `+4,906 B` vs. `MDL`).
     - `short_wgsl_vs_json` held-out `BIT3`: **`11,392 B`** (`-11.3%` smaller than raw `DFL3-zdict` `12,842 B` and **`-22.4%` smaller than `ZST3-tuned` `14,678 B`**).
     - `short_ts_vs_mjs` held-out `BIT3`: **`12,262 B`** (`-8.9%` smaller than `DFL3-zdict` `13,458 B` and **`-20.7%` smaller than `ZST3-tuned` `15,459 B`**).

## Verification

```bash
/usr/bin/python3 -m py_compile vmm_subset_polish.py transfer_vmm.py evaluate_vmm_rung3.py evaluate_transfer_vmm_2x2.py test_vmm_subset.py
/usr/bin/python3 -B test_vmm_subset.py
```

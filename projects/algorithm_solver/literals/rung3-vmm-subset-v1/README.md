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

## Verification

```bash
/usr/bin/python3 -m py_compile vmm_subset_polish.py evaluate_vmm_rung3.py test_vmm_subset.py
/usr/bin/python3 -B test_vmm_subset.py
```

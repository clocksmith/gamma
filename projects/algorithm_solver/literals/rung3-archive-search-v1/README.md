# BITS Rung 3 Kill-Gate Benchmark: Full-Archive MDL Search & Matched Random Access (`rung3-archive-search-v1`)

Tests whether a dictionary search that explicitly prices **full archive bytes** (`dictionary +
canonical Huffman tables + payload`) and prunes absorbed intermediate entries can advance BITS
to Rung 3 under matched search budgets and **serialized, round-trip-verified single-file random
access** (`BIT3` vs. `ZST3`), kept strictly separate from `../codenet-replication-v1/` and
`dcc-v5`.

## What Was Built & Tested

1. **`archive_search.c` (`mdl-archive-prune`):**
   - Compiles against `../fixed-source-v3/engine.c` (`#define ENGINE_NO_MAIN`, zero edits to
     `fixed-source-v3/`).
   - Fixes `engine.c` `greedy-byte`'s dimensional mismatch (`gain / (1 + len)` tokens/byte) by
     pricing net archive bit gain $\Delta B_{\text{pay}}(c) - 8(1 + |c| + \tau)$ at each step
     ([Apostolico & Lonardi, *Proc. IEEE* 88(11):1733–1744, 2000](https://doi.org/10.1109/5.892709)),
     then runs forward-backward omission loss + frequency counting in C to prune absorbed
     intermediate entries (`285–724` entries pruned) and refill freed slots within the same
     wall-clock cap.
2. **`indexed_archive.py` (`BIT3` binary random-access container):**
   - Serializes self-contained `BIT3` archives packing `|D|` dictionary entries, two `(|D|+1)`-byte
     canonical Huffman tables, and a `4 B/file` seek table (`1`-bit language stream + `31`-bit
     exact start bit offset).
   - Verifies true $O(|d|)$ single-file random-access decode (`decode_random_access_file`, tested
     in reverse file order with zero sequential state dependence) against matched `ZST3` bundled
     `zstd -19 --train` (8 KiB shared dictionary + `4 B/file` frame-offset index).

## Empirical Verdict: Rung 3 Static Order-0 Dictionary Search Kill Gate Triggered

From `results/rung3_archive_search_results.json` (serialized random-access totals in bytes):

| Corpus (`train -> held-out`) | `greedy-byte + MDL` | `greedy-entry + MDL` | `mdl-archive-prune` | `zstd -19 --train` (8 KiB `ZST3`) | Verdict |
|---|---:|---:|---:|---:|---|
| CodeNet Py/JS (`200 -> 200` pairs) In-Sample | 89,063 | **86,026** | 86,545 | 91,055 | BITS wins short (`~650 B`) files in-sample |
| CodeNet Py/JS (`200 -> 200` pairs) Held-Out | 101,336 | 100,268 | 100,778 | **95,432** | **`zstd --train` wins by `4,836–5,346 B`** |
| Untouched Zig/WGSL (`40 -> 40`) In-Sample | 36,204 | 34,573 | 34,789 | **31,668** | **`zstd --train` wins in-sample (`-8.4%`)** |
| Untouched Zig/WGSL (`40 -> 40`) Held-Out | 41,380 | 42,623 | 42,045 | **31,501** | **`zstd --train` wins held-out (`-25.1%`)** |
| Untouched C/TS (`40 -> 40`) In-Sample | 54,985 | 52,828 | 52,957 | **47,858** | **`zstd --train` wins in-sample (`-9.4%`)** |
| Untouched C/TS (`40 -> 40`) Held-Out | 65,020 | 66,822 | 65,470 | **49,587** | **`zstd --train` wins held-out (`-24.3%`)** |

### Key Conclusions

1. **Fixes `greedy-byte` and reduces held-out overfitting on real code, but ties `greedy-entry + MDL` in-sample:**
   `mdl-archive-prune` beats `greedy-byte + MDL` in-sample by `1,415–2,518 B` across all three
   suites and beats `greedy-entry + MDL` on held-out untouched code (`+578 B` on Zig/WGSL,
   `+1,352 B` on C/TS) by pruning file-specific 16-byte phrases, while trailing `greedy-entry + MDL`
   by `0.2%–0.6%` (`129–519 B`) in-sample.
2. **Static order-0 dictionary search cannot reach Rung 3 against `zstd --train`:** Under matched
   serialized `4 B/file` random-access indexes, `zstd -19 --train` (8 KiB) wins held-out transfer
   on every corpus (`4.8–25.1%`) and wins **even in-sample** on `1.2–1.9 kB` production Zig/WGSL
   and C/TypeScript files (`8.4–9.4%`), because per-file LZ77 exploits intra-file identifier
   repetition that no static corpus vocabulary can amortize.
3. **Next research focus:** Close static order-0 search heuristics for Rung 3; focus subsequent
   BITS iterations on (a) predicting the intra-file repetition / document-length crossover between
   static vocabulary coding and `zstd --train` (Rung 2 regime predictor) and (b) dual lower-bound
   archive-byte certificates extending Du & Chen (2026) from token count to two-part archive size.

## Verification

```bash
/usr/bin/python3 -m py_compile indexed_archive.py evaluate_rung3.py test_rung3_archive_search.py
/usr/bin/python3 -B test_rung3_archive_search.py
```

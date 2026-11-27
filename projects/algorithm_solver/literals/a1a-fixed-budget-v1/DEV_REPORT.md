# BITS Experiment Card A1a — Fixed-Budget Vocabulary Selection (Development Report)

**Scope:** CPU development only inside `a1a-fixed-budget-v1/` (branch `bits/a1a-dev`). All training and dev-gate decisions use local CodeNet `primary` (400 files, 259,706 bytes). Local spent dev corpora (`dev`, `fresh`, `fresh2`, `Express`, `ramda`, `TheAlgorithms/Python`) are reported purely as diagnostic description. No frozen experiment folder was modified and no sealed test content was touched.

## Executive Verdict (`dev_gate`)

| Criterion | Status | Summary of Measured Evidence |
| --- | --- | --- |
| Dual header serializer (`A1AF` flat-literal + `A1AD` construction-DAG) & standalone independent decode | **PASS** | All 70 dual-archive (140 `A1AF`/`A1AD`) builds plus 72 `emit_mask` archives verified 100% byte-for-byte via `independent_decode.py` (written strictly from `FORMAT.md`, sharing zero code with `headers.py`). |
| Negative corruption controls (DAG edges, ranks, Kraft sum, payload) | **PASS** | All 6 negative controls (DAG self-edge, DAG valid-index edge swap, merge-rank inversion, duplicate merge rank, Huffman Kraft sum corruption, flat payload bitflip) deterministically rejected. |
| Exact `b_max=1` identity check | **PASS** | `slot` mode reproduced `exact-closed-s1-whole.txt` 4,096 / 4,096 (0 diffs, 225.62 s); `byte` mode reproduced `pair-byte.txt` 2,822 / 2,822 (0 diffs, 363.18 s) and completed the full exact `pair-byte` chain to 8,710 entries. |
| Synthetic shared-ancestor bundle mechanism | **PASS** | `engine_shared_bundle` accepts a single-root straddled bundle (`{ba, baaba}`, gain 15 / 2 = 7.5 vs best pair 5.0) and a multi-root shared-ancestor bundle (`{ba, baaba, baabx}`, gain 40 / 3 = 13.33 vs best single-root 12.5 and best pair 10.0), charging the shared ancestor once. |
| Bundle training dev gate — historical flat-literal bytes (`566 B` / `43,480 B`) | **FAIL** | On CodeNet `primary`, `shared-bundle-byte` accepted **0** multi-node bundles across 8,539 steps (573,831 exact joint-DP bundle evaluations), coinciding with exact `pair-byte`: **+4.86%** (566 B) and **+6.53%** (43,480 B) vs `open-byte` (misses the <= +2.0% gate and does not beat `pair-byte`). |
| Bundle training dev gate — matched emitted slots (`84` / `3,924` fragments) | **FAIL** | `shared-bundle-slot` and `shared-bundle-dag` coincided with `exact-closed`: **+14.55%** (84 slots) and **+24.77%** (3,924 slots) vs `open`, confirming the slot-tax corollary (while using 31.1% and 54.1% smaller `A1AD` headers). |
| Repriced common construction-DAG serializer (`A1AD` header `878 B` / `33,241 B`) | **PASS** | Under common `A1AD` header bytes matching `open@84` (`878 B`) and `open@3924` (`33,241 B`), `shared-bundle-dag` (= `exact-closed`, 0 multi-bundle accepts) beats `pair-byte` (**-2.54%** / **-5.42%**) AND beats the better open reference `open-byte` (**-1.30%** / **-1.87%**) at **both** budgets. **Honest attribution:** this win comes from `A1AD` construction-DAG header repricing removing the flat-literal length penalty, **not** from multi-node bundle firing. |
| Ancestor diagnostics & emission-only disabling (storage DAG retained) | **PASS** | Disabling promoted ancestors for emission only on unseen `dev` (retaining storage DAG via `A1AD` `emit_mask`, independently decoded) increases tokens by **+107.88%** (`slots_large`) to **+141.09%** (`dag_header_large`), showing ancestors are load-bearing generalization fallback pieces rather than dead tax. |
| Normalized single-entry pruning bound (`engine_norm_pruned.c`) | **PASS** | **0 / 4,096** full-chain differences vs `exact-norm-s1-whole.txt`; wall-clock **302.63 s** (including **0.279 s** exact `U(w)` maintenance across 284,438 boundary flips) vs **628.49 s** for `engine_dirty_exact.c` (**2.08x speedup**). Proved and empirically verified (0 violations) the dominance identity `min_i Delta_T(t_i t_{i+1}) + U(w) >= used(w)`. |
| Runtime encoder validation — HF `tokenizers` (live in `.venv`) | **PASS** | Live `tokenizers 0.22.2` verified: 100% byte round-trip, exact replay match, reachable vs rank-shadowed and missing-parent unreachable controls. |
| Runtime encoder validation — `tiktoken` byte ranks | **PART** | Pure-Python byte-rank reachability validator passed all controls and audited frozen vocabularies (`bpe-K4096` 3,924/3,924 reachable; `closed-K4096` 274/3,924 rank-shadowed unreachable; `token-K4096` 3,184/3,924 unreachable). Marked **PART** because package `tiktoken` is not installed in `.venv` or system Python. |
| Lean-framed `zstd` complete-archive & p95 latency codec bar | **PASS** | Measured in-process via C `libzstd 1.5.7` (`--no-dictID --no-check`). On `dev` (270,994 B), `zstd-19` lean 8 KiB dict reaches **90,622 B** complete (p95 = **1.70 us**) vs best `A1AD` complete **97,414 B** (`exact-closed@slots_large`, payload 82,155 B < zstd 82,430 B, break-even `M* = 6.91 MB / 10,205 files`). |

---

## 1. Dual Header Formats (`A1AF` and `A1AD`) & Independent Decoder

Full binary specification: [`FORMAT.md`](FORMAT.md). Encoder: [`headers.py`](headers.py). Standalone decoder (stdlib only, zero shared code): [`independent_decode.py`](independent_decode.py).

- **`A1AF` (flat-literal):** 4B magic + `varint(n)` + `sum(1 + |e|)` literal entries + `n + 2` canonical Huffman code lengths + `varint(f)` + payload.
- **`A1AD` (construction-DAG):** 4B magic + 1B flags (`mode=0` pure-pair DAG with dynamic index width `w_i = max(1, (i-1).bit_length())`, or `mode=1` hybrid pair/literal/list DAG for non-closed open vocabularies; optional `emit_mask` for storage-only ancestors; optional topological `merge_ranks`) + `varint(M)` + `varint(A)` + `A` sorted single-byte leaves + bit-packed node table + `n + 2` canonical Huffman code lengths + `varint(f)` + payload.
- **Header compression under the common `A1AD` serializer (including Huffman code table):**
  - `open@84`: `1,171 B` (`A1AF`, 566 B flat frags) -> **`878 B`** (`A1AD`, hybrid mode, `-25.0%`).
  - `open@3924`: `47,925 B` (`A1AF`, 43,480 B flat frags) -> **`33,241 B`** (`A1AD`, hybrid mode, `-30.6%`).
  - `exact-closed@84`: `944 B` (`A1AF`) -> **`605 B`** (`A1AD`, pure-pair mode, `-35.9%`).
  - `exact-closed@3924`: `30,925 B` (`A1AF`) -> **`15,259 B`** (`A1AD`, pure-pair mode, `-50.7%`).
- **Negative corruption controls (`test_headers.py`):**
  1. `dag_self_edge`: rejected (`corrupted DAG edge at node 93: (93, 0) >= 93`)
  2. `dag_edge_swap`: rejected (`byte mismatch in file 0`)
  3. `rank_inversion`: rejected (`corrupted merge rank order: child node 93 (rank 1) >= parent node 94 (rank 0)`)
  4. `rank_duplicate`: rejected (`duplicate merge rank 0 at node 94`)
  5. `huffman_length_corrupt`: rejected (`invalid prefix code Kraft sum: 4352 != 4096`)
  6. `flat_payload_bitflip`: rejected (`truncated payload bitstream`)

---

## 2. Shared-Ancestor Bundle Selector & Why Emitted Bundles Collapse on CodeNet `primary`

Implementation: [`engine_shared_bundle.c`](engine_shared_bundle.c), driver: [`train_dev.py`](train_dev.py).

- **Exact `b_max=1` identity:**
  - `slot` mode (`b_max=1`): **4,096 / 4,096** E-lines match `closure-holdout-v1/out/exact/exact-closed-s1-whole.txt` with **0 differences** (225.62 s, peak RSS 223.8 MiB).
  - `byte` mode (`b_max=1`): **2,822 / 2,822** E-lines match `closure-holdout-v1/out/bundle/pair-byte.txt` with **0 differences** (363.18 s, peak RSS 226.0 MiB), and completes the full exact `pair-byte` chain to **8,710 entries** (exceeding both `43,480 B` flat literal bytes and `33,241 B` `A1AD` header bytes).
- **Synthetic proof of multi-root shared-ancestor assembly (`train_dev.py`):**
  - On the `NORMALIZED-PAIRS.md` 3-doc straddled gadget, `engine_shared_bundle` accepts `B step=2 size=2 roots=1 ancestors=1 gain=15 cost=2` (`{A:ba, R:baaba}`, score `7.5 > 5.0`).
  - On the 2-root shared-ancestor gadget (`baaba` and `baabx` sharing missing ancestor `ba`), `engine_shared_bundle` accepts `B step=5 size=3 roots=2 ancestors=1 gain=40 cost=3` (`{A:ba, R:baabx, R:baaba}`, score `13.33 > 12.5` single-root `> 10.0` best pair), charging `ba` once across both roots.
- **Outcome on CodeNet `primary` (`b_max=16`, up to 35 KB `A1AD` header / ~8,700 entries):**
  - `shared-bundle-byte`: 8,710 entries, 573,831 exact joint-DP bundle evaluations, **0** multi-bundle accepts (878.98 s). Coincides entry-for-entry with exact `pair-byte`.
  - `shared-bundle-slot`: 8,546 entries, **0** multi-bundle accepts (935.75 s). Coincides entry-for-entry with `exact-closed`.
  - `shared-bundle-dag`: 8,546 entries, **0** multi-bundle accepts (936.28 s). Coincides entry-for-entry with `exact-closed`.
- **Mathematical explanation (telescoping / alignment-penalty barrier):** Writing any closed emitted bundle in topological order $B = \{e_1, \dots, e_m\}$, exact joint gain telescopes as $\Delta(B)/\text{cost}(B) = \bigl(\sum_{j=1}^m \Delta(e_j \mid V_{j-1})\bigr)/\bigl(\sum_{j=1}^m \text{cost}(e_j)\bigr)$. Because this is a weighted average of single-step closed ratios, $B$ can strictly beat the exact optimal single closed pair only when intermediate ancestors suffer positive alignment penalty that descendants overcome. On CodeNet `primary`, no emitted multi-node bundle beats the exact optimal pair. Unlike prior `engine_bundle.c`, this is not a lazy-heuristic collapse; it is an intrinsic property of additive emitted-node pricing on `primary`.

---

## 3. Repriced Common-Serializer Comparison (`eval_dev.py`)

### 3A. Common Construction-DAG Header Budgets (`A1AD` matching `open@84 = 878 B` and `open@3924 = 33,241 B`)

**Small budget (`A1AD` header <= 878 B; open ref = `open-byte`, 131,738 primary tokens):**

| Arm | Frags | Flat Frags (B) | `A1AD` Hdr (B) | Primary Tok | vs Open Ref | vs `pair-byte` | `dev` Tok (diag) | `dev` `A1AD` Complete (B) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `open` | 84 | 566 | 878 | 135,219 | +2.64% | +1.35% | 144,545 | 123,573 |
| `open-byte` | 128 | 522 | 873 | 131,738 | 0.00% | -1.26% | 140,871 | 129,025 |
| `exact-closed` | 168 | 719 | 878 | **130,027** | **-1.30%** | **-2.54%** | **138,589** | 128,650 |
| `pair-byte` (exact) | 168 | 604 | 878 | 133,413 | +1.27% | 0.00% | 141,921 | 132,891 |
| `prefix-bundle-byte` | 168 | 608 | 878 | 133,199 | +1.11% | -0.16% | 141,793 | 132,697 |
| `shared-bundle-byte` | 168 | 604 | 878 | 133,413 | +1.27% | 0.00% | 141,921 | 132,891 |
| `shared-bundle-dag` | 168 | 719 | 878 | **130,027** | **-1.30%** | **-2.54%** | **138,589** | 128,650 |
| `bpe` (DP / native) | 168 | 724 | 878 | 130,429 / 131,043 | -0.99% | -2.24% | 138,627 / 139,174 | 128,748 |
| `greedtok` | 86 | 577 | 876 | 134,461 | +2.07% | +0.79% | 144,153 | **123,158** |
| `pathpiece` | 72 | 529 | 877 | 142,669 | +8.30% | +6.94% | 151,731 | 126,300 |

**Large budget (`A1AD` header <= 33,241 B; open ref = `open-byte`, 38,558 primary tokens):**

| Arm | Frags | Flat Frags (B) | `A1AD` Hdr (B) | Primary Tok | vs Open Ref | vs `pair-byte` | `dev` Tok | `fresh2` | `Express` | `ramda` | `Python` | `dev` `A1AD` Complete (B) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `open` | 3,924 | 43,480 | 33,241 | 39,204 | +1.68% | -2.00% | 65,624 | 59,834 | 81,047 | 101,620 | 184,714 | 118,138 |
| `open-byte` | 6,314 | 44,077 | 33,240 | 38,558 | 0.00% | -3.61% | 57,386 | 52,280 | 68,011 | 83,536 | 145,752 | 116,051 |
| `exact-closed` | 8,147 | 59,295 | 33,238 | **37,836** | **-1.87%** | **-5.42%** | 55,622 | 50,444 | 64,397 | 79,538 | 139,219 | **114,297** |
| `pair-byte` (exact) | 8,147 | 48,271 | 33,238 | 40,003 | +3.75% | 0.00% | **55,538** | **50,395** | **62,609** | **76,543** | **135,052** | 115,261 |
| `shared-bundle-byte` | 8,147 | 48,271 | 33,238 | 40,003 | +3.75% | 0.00% | **55,538** | **50,395** | **62,609** | **76,543** | **135,052** | 115,261 |
| `shared-bundle-dag` | 8,147 | 59,295 | 33,238 | **37,836** | **-1.87%** | **-5.42%** | 55,622 | 50,444 | 64,397 | 79,538 | 139,219 | **114,297** |
| `bpe` (DP / native) | 8,147 | 63,155 | 33,238 | 39,601 / 40,053 | +2.71% | -1.01% | 55,938 / 57,486 | 50,507 | 63,658 | 79,305 | 141,016 | 114,340 |
| `greedtok` | 3,959 | 43,738 | 33,237 | 40,529 | +5.11% | +1.32% | 65,792 | 60,160 | 82,817 | 101,701 | 181,473 | 117,953 |
| `pathpiece` | 4,947 | 63,010 | 33,236 | 69,077 | +79.15% | +72.68% | 76,214 | 68,310 | 75,906 | 97,457 | 182,200 | 125,380 |

*(Prior `prefix-bundle-byte` / `prefix-bundle-slot` chains in frozen `closure-holdout-v1/out/bundle/` stopped at 44,000 flat bytes = 30.2 KB / 24.2 KB `A1AD` header and therefore do not reach 33,241 B; they appear at all flat-fragment and emitted-slot budgets below.)*

### 3B. Historical Flat-Literal Fragment Bytes (`566 B` / `43,480 B`) & Matched Emitted Slots (`84` / `3,924`)

| Arm | `566 B` flat (Primary / vs ref) | `43,480 B` flat (Primary / vs ref) | `84` slots (Primary / vs open) | `3,924` slots (Primary / vs open) | `3,924` slots `dev` `A1AD` Complete (B) |
| --- | --- | --- | --- | --- | ---: |
| `open` | 135,219 (+4.58%) | 39,204 (+1.19%) | **135,219** (0.00%) | **39,204** (0.00%) | 118,138 |
| `open-byte` | **129,293** (0.00%) | **38,742** (0.00%) | 145,720 (+7.77%) | 47,123 (+20.20%) | 101,714 |
| `exact-closed` | 138,792 (+7.35%) | 42,517 (+9.74%) | 154,890 (+14.55%) | 48,916 (+24.77%) | **97,414** |
| `pair-byte` (exact) | 135,575 (+4.86%) | 41,272 (+6.53%) | 157,156 (+16.22%) | 51,177 (+30.54%) | 99,531 |
| `prefix-bundle-byte` | 135,557 (+4.84%) | 41,607 (+7.39%) | 157,145 (+16.21%) | 51,456 (+31.25%) | 99,614 |
| `shared-bundle-byte` | 135,575 (+4.86%) | 41,272 (+6.53%) | 157,156 (+16.22%) | 51,177 (+30.54%) | 99,531 |
| `shared-bundle-dag` | 138,792 (+7.35%) | 42,517 (+9.74%) | 154,890 (+14.55%) | 48,916 (+24.77%) | **97,414** |
| `bpe` (DP) | 139,732 (+8.07%) | 44,276 (+14.28%) | 155,571 (+15.05%) | 50,435 (+28.65%) | 98,056 |
| `greedtok` | 135,669 (+4.93%) | 40,629 (+4.87%) | 135,257 (+0.03%) | 40,691 (+3.79%) | 117,571 |
| `pathpiece` | 140,738 (+8.85%) | 69,084 (+78.32%) | 137,043 (+1.35%) | 69,078 (+76.20%) | 116,383 |

### 3C. Stock Deployment Controls (Common DP vs Native Encoders on `primary` / `dev`)

- **Longest-match (AC/trie greedy) vs common min-token DP on `dev` (`dag_header_large` / `slots_large`):**
  - `open@3924`: DP `65,624` vs longest-match `69,077` (`+5.26%`).
  - `exact-closed@3924`: DP `60,892` vs longest-match `63,988` (`+5.08%`); at `dag_header_large` (8,147 frags): DP `55,622` vs longest-match `58,926` (`+5.94%`).
  - `bpe@3924`: DP `61,922` vs native BPE merge replay `63,221` (`+2.10%`) vs longest-match `64,201` (`+3.68%`).
  - `bpe@dag_header_large` (8,147 frags): DP `55,938` vs native BPE merge replay `57,486` (`+2.77%`).
- **SentencePiece Unigram (`sentencepiece 0.2.1`, `byte_fallback=True`, 100% UTF-8 dev round-trip):**
  - `sp-unigram-440` (107 frags, `A1AD` 962 B): primary DP `175,080` / native Viterbi `175,374`; dev DP `182,931` / native `183,217`.
  - `sp-unigram-4280` (3,936 frags, `A1AD` 29,544 B): primary DP `70,862` / native `72,493`; dev DP `94,850` / native `97,306`. (Line-delimited SentencePiece training cannot learn cross-newline indentation tokens such as `\n    `.)
- **Stock HF `tokenizers` ByteLevel BPE (`ByteLevel` regex pre-tokenizer, 100% UTF-8 dev round-trip):**
  - `hf-bytelevel-bpe-340` (84 frags, `A1AD` 605 B): primary DP `166,555` / native `168,386`; dev DP `175,401` / native `177,418`.
  - `hf-bytelevel-bpe-4180` (3,205 frags — capped by word-level pre-tokenization, `A1AD` 12,383 B): primary DP `98,065` / native `99,266`; dev DP `110,505` / native `111,694`.

### 3D. Lean-Framed `zstd` Codec Comparison & Break-Even Horizon $M^*$ (Unseen `dev`, 400 files, 270,994 B)

| Codec / Arm | Header / Dict (B) | Payload (B) | Complete (B) | Complete Bits | Random-Access (B) | Record Decode p50 / p95 (us) | Basis |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `zstd -19` lean, 8 KiB dict | 8,192 | 82,430 | **90,622** | **724,976** | **91,283** | 0.50 / **1.70** | C `libzstd 1.5.7` |
| `zstd -19` std, 8 KiB dict | 8,192 | 85,630 | 93,822 | 750,576 | 94,494 | 0.60 / 1.93 | C `libzstd 1.5.7` |
| `zstd -19` lean, 32 KiB dict | 32,768 | 76,732 | 109,500 | 876,000 | 110,148 | 0.42 / 1.50 | C `libzstd 1.5.7` |
| `zstd -19` lean, no dict | 0 | 129,225 | 129,225 | 1,033,800 | 129,977 | 1.75 / 3.10 | C `libzstd 1.5.7` |
| `exact-closed` / `shared-bundle-dag` @ `slots_large` (`A1AD`) | 15,259 | 82,155 | **97,414** | 779,312 | 98,176 | 383.2 / 1,583.9 | Pure-Python independent decoder |
| `shared-bundle-dag` @ `dag_header_large` (`A1AD`) | 33,238 | **81,059** | 114,297 | 914,376 | 115,054 | 350.1 / 1,449.6 | Pure-Python independent decoder |
| `open` @ `slots_large` (`A1AD` / `A1AF`) | 33,241 / 47,925 | 84,897 | 118,138 / 132,822 | 945,104 / 1,062,576 | 118,895 / 133,579 | 405.4 / 1,666.0 | Pure-Python independent decoder |

**Break-even horizons $M^*$ on `dev`:**
- `A1AD` vs `A1AF` (same arm): `A1AD` **strictly dominates** at every corpus size ($M^* = 0$, identical payload and strictly smaller header).
- `shared-bundle-dag` (`exact-closed`) vs `open` under `A1AD` at both `dag_header_large` and `slots_large`: `shared-bundle-dag` **strictly dominates** on both header and payload ($M^* = 0$).
- `exact-closed@slots_large` (`A1AD`, 15,259 B header, 82,155 B payload) vs `zstd-19` lean 8 KiB dict (8,192 B dict, 82,430 B payload): `A1AD` has 275 B smaller payload on `dev` and breaks even at **$M^* = 6.91\text{ MB}$ (`10,205` files)**; vs `zstd-19` lean 32 KiB dict, `A1AD` wins below **$M^* = 875\text{ KB}$ (`1,292` files)**!
- `shared-bundle-dag@dag_header_large` (`A1AD`, 33,238 B header, 81,059 B payload) vs `zstd-19` lean 8 KiB dict: `A1AD` has 1,371 B smaller payload and breaks even at **$M^* = 4.94\text{ MB}$ (`7,297` files)**.

---

## 4. Ancestor Diagnostics & Emission-Only Disabling

| Arm @ Budget | Multi Nodes | Promoted Ancestors | Shared (deg >= 2) | Emitted (prim / dev) | Unused (prim / dev) | Joint Disable `unused_prim` (`dev` tok / delta) | Joint Disable ALL Promoted (`dev` tok saved) | Joint Disable Shared (`dev` tok saved) | Indiv Positive / Sum Saved (`dev`) |
| --- | ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: | --- |
| `shared-bundle-dag@slots_small` | 84 | 39 | 8 | 39 / 37 | 0 / 2 | 163,317 (+0.00%) | +32,969 (+20.19%) | +4,647 (+2.85%) | 36/39 (sum 14,373) |
| `shared-bundle-dag@slots_large` | 3,924 | 1,974 | 849 | 1,589 / 1,471 | 385 / 503 | 61,253 (+0.59%) | **+65,692 (+107.88%)** | **+30,506 (+50.10%)** | 1,376/1,974 (sum 19,384, med 4, p95 37, max 140) |
| `shared-bundle-dag@dag_header_large` | 8,147 | 4,101 | 1,855 | 2,801 / 2,511 | 1,300 / 1,590 | 57,092 (+2.64%) | **+78,479 (+141.09%)** | **+44,969 (+80.85%)** | 2,274/4,101 (sum 18,977, med 1, p95 21, max 105) |
| `shared-bundle-byte@dag_header_large` | 8,147 | 3,504 | 1,660 | 2,397 / 2,316 | 1,107 / 1,188 | 56,994 (+2.62%) | **+64,531 (+116.19%)** | **+35,232 (+63.44%)** | 2,051/3,504 (sum 16,932, med 1, p95 22, max 104) |
| `bpe@dag_header_large` | 8,147 | 3,742 | 1,598 | 2,621 / 2,337 | 1,121 / 1,405 | 57,045 (+1.98%) | **+73,217 (+130.89%)** | **+36,357 (+65.00%)** | 2,086/3,742 (sum 18,316, med 1, p95 21, max 105) |

Top individual unseen-`dev` token-saving ancestors in `shared-bundle-dag@slots_large`: `', '` (DAG out-degree 60, +140 tokens when disabled), `' = '` (deg 89, +137), `'dp'` (deg 6, +136). Disabling `unused_on_primary` ancestors via `emit_mask` does **not** improve `dev` complete bytes (`97,414 B -> 97,719 B` at `slots_large`) because the 512 B emit mask exceeds the 385 B code-table savings and some train-unused ancestors are emitted on unseen `dev`.

---

## 5. Normalized Single-Entry Pruning Bound (`engine_norm_pruned.c`)

Implementation: [`engine_norm_pruned.c`](engine_norm_pruned.c), verifier: [`test_norm_pruning.py`](test_norm_pruning.py).

- **Exactness:**
  - `NORMALIZED-PAIRS.md` 6-doc counterexample (`abcd`, non-pair wins): `score = 3.0 <= min_pair_gain(0) + U(6) = 6` (sound).
  - 16 synthetic corpora (625 E-lines, `--verify-u-every 1`): **0 differences** vs unpruned `engine_norm.c`, exact `U(w)` every step.
  - Full CodeNet `primary` chain (`4,096` entries): **0 / 4,096 differences** vs `closure-holdout-v1/out/exact/exact-norm-s1-whole.txt` (SHA-256 `c3c026e9...`).
- **Measured work (including exact `U(w)` count maintenance):**
  - Full 4,096 chain: **302.63 s** wall-clock (`0.330 s` enumerate, `150.193 s` Phase 1 closed heap, `131.745 s` Phase 2 non-pair search, **`0.279 s`** incremental `U(w)` maintenance across `284,438` boundary flips, peak RSS `270.3 MiB`) vs `628.49 s` for frozen `engine_dirty_exact.c` (**2.08x speedup**).
  - K=300 prefix comparison: unpruned `engine_norm.c` `13.733 s` -> pure U-bound + Phase-1 closed heap `10.005 s` (**1.37x**) -> U-bound + lazy dirty non-pair caching `8.989 s` (**1.53x**).
- **Dominance theorem proved & verified (`0` violations across 6.10B checks):**
  For every candidate $w$ with $s_V(w) \ge 3$, let $S$ be a maximum pairwise non-overlapping set of occurrences ($|S| = \text{used}(w)$), split into aligned $S_A$ and unaligned $S_U$ with respect to $P_0$. Since $|S_A| \le \min_i \Delta_T(t_i t_{i+1})$ and $|S_U| \le U(w)$, we have
  $$\min_i \Delta_T(t_i t_{i+1}) + U(w) \;\ge\; |S_A| + |S_U| \;=\; \text{used}(w)$$
  identically. Accordingly, `pruned_u_vs_used = 0` on every step; the 2.08x full-chain speedup comes from separating Phase-1 active closed pairs plus lazy dirty-document non-pair caching (`87,799,431` dirty non-pair prunes), not from `U(w)` tightening below the free static bound `used(w)`.

---

## 6. Runtime Encoder Validation (`validate_encoders.py`)

- **Hugging Face `tokenizers 0.22.2` (live in `.venv` — `PASS`):**
  - Positive reachable merge `[(a,b),(ab,c)]` forms `abc` with 100% round-trip.
  - Rank-shadowed unreachable merge `[(b,c),(a,b),(ab,c)]` produces `['a','bc']` and never forms `abc`.
  - Missing-parent merge `[(ab,c)]` is rejected by constructor (`Token 'ab' out of vocabulary`).
  - Live replay on 25 CodeNet `dev` files for `bpe-K256/K4096` and `closed-K256/K4096`: 100% byte-for-byte round-trip and 5/5 exact token-stream match against reference BPE replay.
- **`tiktoken`-style byte-rank reachability validator (`PART` — missing `tiktoken` package):**
  - Positive, shadowed-dead-token (`ab=256, bc=257, bcd=258, abcd=259` where `abcd` is closed as `a+bcd` yet unreachable because `ab` blocks `bc`), unclosed, and rank-inversion controls all passed.
  - Real frozen vocabulary audit under `tiktoken` byte-rank replay:
    - `bpe-K256`: **84 / 84** reachable (0 unclosed, 0 unreachable).
    - `bpe-K4096`: **3,924 / 3,924** reachable (0 unclosed, 0 unreachable).
    - `closed-K256`: **82 / 84** reachable (0 unclosed, **2** rank-shadowed unreachable: `' in '`, `');\n    '`).
    - `closed-K4096`: **3,650 / 3,924** reachable (0 unclosed, **274** = 7.0% rank-shadowed unreachable, e.g. `'input()'`, `'for i in range('`).
    - `token-K4096` (open): **740 / 3,924** reachable (**2,762** unclosed, **3,184** unreachable).
  - Finding: constituent closure alone is **not** sufficient for greedy byte-rank reachability; `exact-closed` leaves 7.0% of its K=4096 vocabulary unreachable under `tiktoken` greedy rank replay even though every entry is closed and emitted by exact shortest-path DP.

---

## 7. Verification Entrypoint

Run fast end-to-end verification:
```bash
/Users/xyz/deco/gamma/.venv/bin/python replay.py check --report out/replay_check.json
```
Exit status is `0` when every check passes (with `tiktoken_byte_ranks` reported transparently as `PART` because `tiktoken` is not installed; `--strict` turns `PART` into failure).

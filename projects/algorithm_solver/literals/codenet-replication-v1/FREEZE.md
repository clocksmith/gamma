# Frozen Replication Protocol (`codenet-replication-v1`)

**Freeze Timestamp:** 2026-11-24T20:26:00Z (committed BEFORE running any dictionary search on CodeNet)
**Manifest SHA-256:** `4796ac6afda3ff28c18a452e4f71852ba91366c5aa3427748a070a3417f5cf29`
**Upstream Dataset & Revision:** IBM Project CodeNet v1.0.0 (`CDLA-Permissive-2.0`), Hugging Face mirror `iNeil77/CodeNet` at pinned commit `1e28cfa9f8eb2df763ad2514af11afd6e92dd07a`

## 1. Role of This Corpus vs. Background Corpus

- **Main evidence:** Public paired, judge-accepted IBM Project CodeNet Python 3 and JavaScript corpora (`primary` and `secondary`, zero problem overlap).
- **Background only (not replication evidence):** Private 400-problem `fixed-source-v3` corpus (`264,908` bytes), verified via its source-free tables in `../fixed-source-v3/results/`. At `K = 4,096`, `L = 16`, `s1-whole`, uncapped on that private corpus, Design B wins at `81,079` bytes (`A = 83,440`, `C = 81,841`, `token-best A = 100,965`).

## 2. Verified Population & Frozen Sampling Rule

Full scan of `iNeil77/CodeNet` (`JavaScript` 57,805 rows / 25,223 `Accepted` / 1,805 problems; `Python` 3,281,911 rows / 1,794,079 `Accepted` / 3,080 problems):
- Any-runtime `Accepted` Python/JavaScript overlap: **1,797 problems**.
- Eligible overlap (`status == 'Accepted'`, pure Python 3 runtimes vs. Node.js/JavaScript runtimes, valid UTF-8, `64 <= bytes <= 4096`, zero NUL bytes): **1,757 problems**.

Deterministic selection (zero manual curation or outcome inspection):
1. Rank all 1,757 eligible overlapping problems by ascending `SHA-256("bits-codenet-replication-v1:" + p_id)`.
2. Assign ranks `0..199` to **`primary`** (200 paired problems, 400 files: Python 3 = `93,265` B, JavaScript = `166,441` B, total = **`259,706` B**) and ranks `200..399` to **`secondary`** (200 disjoint paired problems, 400 files: Python 3 = `93,356` B, JavaScript = `177,638` B, total = **`270,994` B**).
3. Within each `(p_id, language)`, sort eligible submissions by `(byte_length, s_id)` and pick the lower-median submission `eligible[(len - 1) // 2]`.

## 3. Exact Accounting, Search Grid, and Equal Budgets

Accounting matches `../fixed-source-v3/encoded.py` byte-for-byte:
- `dict_bytes = sum(1 + len(entry))`
- `table_bytes = (|D| + 1)` for 1-table designs (Design A, each Design C language component) and `2 * (|D| + 1)` for Design B (one code-length byte per entry plus one EOF symbol per table).
- `routing_bytes = 0` for Design A, `4` for Designs B and C.
- `payload_bytes = ceil(total_huffman_bits / 8)` (for B and C, `ceil(bits_py / 8) + ceil(bits_js / 8)`).
- `total_bytes = dict_bytes + table_bytes + routing_bytes + payload_bytes`.

Search grid & equal search budget:
- Primary slot budgets: `K in {256, 1024, 4096}` at `L = 16`, uncapped (`B = None`), under `s1-whole`.
- Full measurement grid: `K in {128, 256, 512, 1024, 2048, 4096}`, `B in {4096, 8192, 16384, 32768, 65536, None}`, policies `s1-whole`, `s2-nowhole`, `p2-nowhole`, `L in {8, 16, 32}` on `primary` and `L = 16` on `secondary`.
- Equal-budget arms (`../fixed-source-v3/engine.c`, `Kmax = 4096`, `LIMIT_SECONDS = 300`): `greedy-entry`, `greedy-byte`, `greedtok`, `pathpiece` (32,768-merge BPE seed), `bpe`, `freq-occ`, `freq-doc`, plus policy monotonicity floors and the Design-C union floor for Designs A/B.

## 4. Exact Byte-Optimal Segmentation Rule

For every feasible `L = 16` cell (and across all arms + union candidates at uncapped `L = 16` cells), re-segment each candidate dictionary from its token-optimal parse using exact shortest-path minimum-bit-length DP (`byte_encode.optimize_byte_segmentation`) iterated to monotone fixed point (`bits_t < bits_{t-1}`). Record the exact byte change, every excluded/infeasible cell, and every ranking reversal between Designs A, B, C, and token-best A.

## 5. Detectable Effect & Pre-Registered Decision Rules

- **Detectable effect threshold:** `>= 1.0%` relative total-byte difference (`>= 100` bps) on matched feasible cells (`>= ~800` bytes on a `~80,000` B encoded corpus, far above 1-byte rounding).
- **R1 (Design B ordering):** Under `s1-whole`, `L = 16`, uncapped at `K in {256, 1024, 4096}`, check whether Design B is strictly smallest (`B < A` and `B < C`) on both `primary` and `secondary`, report exact % margins, and report win rate plus every excluded/infeasible cell across the full `L = 16` grid.
- **R2 (Token-min vs. byte-min divergence):** At `K = 4,096`, `L = 16`, `s1-whole`, uncapped, check whether minimum-token Design A exceeds minimum-byte Design A by `>= 1.0%`.
- **R3 (Survival under exact byte-optimal segmentation):** Check whether R1 and R2 survive exact bit-length-minimizing fixed-point DP. Report every ranking reversal explicitly.
- **R4 (Information-theoretic table-overhead crossover — Rung 4 DCC):** Check whether the exact weighted Jensen-Shannon / mutual-information identity `I(Symbol; Language) / 8` vs. `|D| + 5` extra header+routing bytes predicts the sign and crossover of Design B vs. Design A across `K` and sub-corpus sizes `N_pairs in {5, 10, 20, 40, 60, 100, 150, 200}`.
- **R5 (Practical runtime & honest Rung 5 lossless baseline gate):** Benchmark wall-clock encode/decode (`ms`, `MB/s`) and total bytes against `zlib -9`, `zstd -19`, `zstd -19 --train` (shared and per-language dicts), `brotli -11`, and `xz -6` (per-file random-access, solid archive, and `primary -> secondary` out-of-sample transfer). Claim Rung 5 **only** if a practical BITS encoder materially beats strong general-purpose lossless baselines across both corpora without unacceptable runtime/memory costs; otherwise report explicitly that BITS does not clear Rung 5.

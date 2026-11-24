# BITS CodeNet Replication Artifact (`codenet-replication-v1`)

Self-contained public replication and verification bundle for **BITS** (token-minimal vs. byte-minimal objective bloat, shared dictionary + separate per-language code tables, exact byte-optimal DP parsing, information-theoretic table-amortization crossover, and lossless baseline boundary) on paired, judge-accepted Python 3 and JavaScript programs from IBM Project CodeNet v1.0.0 (`CDLA-Permissive-2.0`).

## Contents

- `FREEZE.md`: Pre-execution frozen protocol (sampling rule, grid, practical `1.0%` size-materiality threshold, byte-optimal DP rule, decision rules, and honest Rung 5 gate), committed at `gamma@c1ac36122` before running any dictionary search.
- `NOTICE`: IBM Project CodeNet (`CDLA-Permissive-2.0`) attribution notice.
- `manifest.json`: Full CodeNet overlap verification plus per-file `p_id`, `s_id`, `u_id`, `original_language`, byte count, and SHA-256 for both frozen disjoint splits (`primary`: 200 pairs = 400 files; `secondary`: 200 disjoint pairs = 400 files).
- `corpus/`: The 800 frozen public source files (`primary/{python,javascript}` and `secondary/{python,javascript}`).
- `dictionaries/`: Hex-encoded verified headline dictionaries (`K in {256, 1024, 4096}`, `L = 16`, `s1-whole`, uncapped) for independent bit-for-bit verification.
- `results/`: Verified JSON tables (`codenet_results.json` and `baselines.json`).
- `byte_encode.py`: Zero-dependency Python 3 standard-library implementation of canonical Huffman coding, exact bit-length-minimizing fixed-point DP parsing, KL / Jensen-Shannon mutual-information decomposition, and wall-clock encode/decode benchmarking.
- `extract_codenet.py`: Deterministic streaming extractor from `iNeil77/CodeNet` (pinned revision `1e28cfa9f8`).
- `run_replication.py`: Compiles `../fixed-source-v3/engine.c`, runs all 7 equal-budget arms, scores token-min and exact byte-min parsing, computes KL/JS crossover curves, and benchmarks encode/decode speed.
- `benchmark_baselines.py`: Benchmarks `zlib -9`, `zstd -19`, `zstd -19 --train` (shared and per-language dictionaries), `brotli -11`, and `xz/lzma -6` in per-file random-access, solid-archive, and out-of-sample `primary -> secondary` transfer modes.
- `verify_bundle.py`: Standalone zero-dependency verifier (Python 3 stdlib only, sharing zero code with `engine.c`).

## Exact Verification Scope: What `verify_bundle.py` Checks vs. What Requires Rerunning

| Claim / Artifact | Checked directly offline by `python3 verify_bundle.py` (~25s, stdlib only) | Requires rerunning full pipeline |
|---|---|---|
| 800 frozen source files, sizes, SHA-256, zero split overlap, SHA-256 rank order | **Yes** (against `manifest.json`) | Rerunning `extract_codenet.py` re-verifies upstream Hugging Face Parquet overlap (`1,797` / `1,757`) |
| Tables I & II headline totals (`K in {256, 1024, 4096}`, A/B/C/tok-best, token-min & byte-min) | **Yes** (`40` independent bit-for-bit canonical Huffman encode+decode checks + Kraft equality + exact `dict + table + routing + payload` match) | Rerunning `run_replication.py` re-derives the 252 `engine.c` chains from scratch |
| Figure 2 KL/JS mutual information & corpus-size crossover (`N_pairs in {5..200}`) | **Yes** (`22` direct recomputations from raw corpus + exported dictionaries) | Rerunning `run_replication.py` also re-scores intermediate `K in {512, 2048}` |
| Full `72/72` (`L=16`) & `216/216` (`L in {8,16,32}`) grid win rates, `0` reversals, Table III per-arm totals | Stored in `results/codenet_results.json` (not re-searched by verifier) | **Yes** (`python3 run_replication.py`) |
| Table IV & Figure 3 lossless baselines (`zlib`, `zstd`, `zstd --train`, `brotli`, `xz`), OOS transfer, and wall-clock MB/s | Stored in `results/baselines.json` and `codenet_results.json` | **Yes** (`python3 benchmark_baselines.py` + `run_replication.py`) |
| Permitted source-free `fixed-source-v3` background tables (`81,079` B min, `120/120` B wins) | **Yes** (against `../fixed-source-v3/results/encoded.json.gz`) | Private v3 sources are non-redistributable (background only) |

## One-Command Verification (No Third-Party Dependencies)

```bash
python3 verify_bundle.py
```

## Full Reproduction From Frozen Corpus

```bash
python3 test_byte_encode.py
python3 run_replication.py
python3 benchmark_baselines.py
python3 verify_bundle.py
```

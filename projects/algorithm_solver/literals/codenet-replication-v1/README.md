# BITS CodeNet Replication Artifact (`codenet-replication-v1`)

Self-contained public replication and verification bundle for **BITS** (dictionary sharing, separate per-language code tables, byte-optimal segmentation, information-theoretic table crossover, and lossless baseline comparison) on paired, judge-accepted Python 3 and JavaScript programs from IBM Project CodeNet v1.0.0 (`CDLA-Permissive-2.0`).

## Contents

- `FREEZE.md`: Pre-execution frozen protocol (sampling rule, grid, detectable effect, byte-optimal segmentation rule, decision rules, and honest Rung 5 gate), committed before running dictionary search.
- `NOTICE`: IBM Project CodeNet (`CDLA-Permissive-2.0`) attribution notice.
- `manifest.json`: Full CodeNet overlap verification plus per-file `p_id`, `s_id`, `u_id`, `original_language`, byte count, and SHA-256 for both frozen disjoint splits (`primary`: 200 pairs = 400 files; `secondary`: 200 disjoint pairs = 400 files).
- `corpus/`: The 800 frozen public source files (`primary/{python,javascript}` and `secondary/{python,javascript}`).
- `dictionaries/`: Hex-encoded verified headline dictionaries (`K in {256, 1024, 4096}`, `L = 16`, `s1-whole`, uncapped) for independent bit-for-bit verification.
- `results/`: Verified JSON tables (`codenet_results.json` and `baselines.json`).
- `byte_encode.py`: Zero-dependency Python 3 standard-library implementation of exact canonical Huffman coding, exact bit-length-minimizing fixed-point DP segmentation, KL / Jensen-Shannon mutual-information decomposition, and wall-clock encode/decode benchmarking.
- `extract_codenet.py`: Deterministic streaming extractor from `iNeil77/CodeNet` (pinned revision).
- `run_replication.py`: Compiles `../fixed-source-v3/engine.c`, runs all 7 equal-budget arms, scores token-min and exact byte-min segmentation, computes KL/JS crossover curves, and benchmarks encode/decode speed.
- `benchmark_baselines.py`: Benchmarks `zlib -9`, `zstd -19`, `zstd -19 --train` (shared and per-language dictionaries), `brotli -11`, and `xz/lzma -6` in both per-file random-access and solid-archive modes, plus out-of-sample `primary -> secondary` transfer.
- `verify_bundle.py`: Standalone zero-dependency verifier (Python 3 stdlib only, sharing zero code with `engine.c`) that checks every SHA-256, packs and decodes real canonical Huffman bitstreams bit-for-bit across all headline dictionaries, checks KL/JS identities, and verifies the permitted source-free `../fixed-source-v3/results/` background tables.

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

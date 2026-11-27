# A1a Sealed Fresh-Corpus Report: `A1AD` Construction-DAG Headers & Native Encoder Controls

## Gate Summary

- **Frozen Artifacts Verified (`PREREGISTRATION_DAG_ENCODERS.md`):** 5/5 SHA-256 exact match (`FORMAT.md`, `headers.py`, `independent_decode.py`, `validate_encoders.py`, `requirements-tiktoken.txt`).
- **Closed Arm Note:** Multi-node shared bundle (`A1AB`) remained CLOSED after its CodeNet `primary` FAIL and was NOT carried into this sealed run.
- **Gate 1 (100% Byte-Exact Independent Decode + 6 Negative Corruption Controls):** **`PASS`** (0 mismatches across all 40 archives; 6/6 corruption controls rejected with `FormatError`).
- **Gate 2a (`A1AD < A1AF` with 0 Payload Diff across all 5 arms x 4 budgets x 2 corpora):** **`PASS`**.
- **Gate 2b (`exact-closed A1AD` vs `open A1AD` at large `A1AD` budget `<= 33,241 B`):**
  - `fresh-js-24repos` (24 repos, 345 files, 1,109,832 B): complete bits `-8.627%` (wins `23/24`, two-sided sign `p=0.000003`), min-DP tokens `-21.835%` (`24/24`, `p=0.000000`) -> **`PASS`**
  - `fresh-py-12repos` (12 repos, 131 files, 775,336 B): complete bits `-8.621%` (wins `12/12`, two-sided sign `p=0.000488`), min-DP tokens `-23.148%` (`12/12`, `p=0.000488`) -> **`PASS`**
- **Gate 3 (Live Deployment Encoders — HF `tokenizers`, `sentencepiece`, live pinned `tiktoken==0.14.0`):** **`PASS`** (`shadowing_discrepancies = 0`, 0 UTF-8 round-trip failures across 476/476 files, 0 token-stream parity mismatches across 476/476 files).
- **Important Comparative Finding (`bpe` vs `exact-closed` & `zstd -19`):** On fresh external codebases at matched `A1AD` header budgets, `exact-closed` beats `open` by `-8.6%` complete bits (`-21.8%` to `-23.1%` min-DP tokens), while plain `bpe` (also 100% pair-DAG closed) beats `exact-closed` at the large budget (`5,538,424` vs `5,642,152` b on JS, `3,667,888` vs `3,734,296` b on Py at `dag_header_large`) and in 7 of 8 budget x corpus cells overall (`exact-closed` is slightly ahead in the 1 remaining cell: `dag_header_small` on `fresh-py-12repos`, `3,535,904` vs `3,540,688` b, `-4,784` b). Plain `bpe` also has **0 shadowed tokens** in native `tiktoken` (vs **852 / 8,036** shadowed for `exact-closed`), while lean-framed `zstd -19` remains strictly smaller (`2.74M` b JS, `1.88M` b Py) and ~10x faster to decode in C.

## Large `A1AD` Budget (`<= 33,241 B`) Complete Bits vs Lean-Framed `zstd -19`

### `fresh-js-24repos` (345 files, 1,109,832 raw bytes)

| Arm / Codec | Fragments | `A1AF` Header (B) | `A1AD` Header (B) | Header Save | `A1AF` Complete Bits | `A1AD` Complete Bits | Min-DP Tokens | Decode p95 (us) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `open` (hybrid) | 3,924 | 47,925 | 33,241 | -30.6% | 6,292,296 | **6,174,824** | 567,111 | 24764.3 (Py) |
| `open-byte` (hybrid) | 6,314 | 50,912 | 33,240 | -34.7% | 6,165,200 | **6,023,824** | 467,133 | 15104.8 (Py) |
| `exact-closed` (pair) | 8,147 | 67,963 | 33,238 | -51.1% | 5,919,952 | **5,642,152** | 443,280 | 13354.0 (Py) |
| `pair-byte` (pair) | 8,147 | 56,939 | 33,238 | -41.6% | 5,887,408 | **5,697,800** | 430,831 | 14329.8 (Py) |
| `bpe` (pair) | 8,147 | 71,823 | 33,238 | -53.7% | 5,847,104 | **5,538,424** | 443,986 | 12389.2 (Py) |
| zstd-19 lean (8K primary dict) | n/a | 8,192 | 8,192 | 0.0% | 2,741,728 | **2,741,728** | n/a | 12.2 (C) |
| zstd-19 lean (32K primary dict) | n/a | 32,768 | 32,768 | 0.0% | 2,919,472 | **2,919,472** | n/a | 12.4 (C) |
| zstd-19 lean (no dict) | n/a | 0 | 0 | 0.0% | 2,812,536 | **2,812,536** | n/a | 10.9 (C) |

- Honest `zstd-19` comparator note: `exact-closed (A1AD)` vs `zstd-19 lean (8K dict)` status = `b_dominates` (M* = `None` B); `zstd-19` remains strictly smaller in complete bits on these fresh corpora.

### `fresh-py-12repos` (131 files, 775,336 raw bytes)

| Arm / Codec | Fragments | `A1AF` Header (B) | `A1AD` Header (B) | Header Save | `A1AF` Complete Bits | `A1AD` Complete Bits | Min-DP Tokens | Decode p95 (us) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `open` (hybrid) | 3,924 | 47,925 | 33,241 | -30.6% | 4,204,088 | **4,086,616** | 370,608 | 28966.2 (Py) |
| `open-byte` (hybrid) | 6,314 | 50,912 | 33,240 | -34.7% | 4,069,152 | **3,927,776** | 298,161 | 17909.3 (Py) |
| `exact-closed` (pair) | 8,147 | 67,963 | 33,238 | -51.1% | 4,012,096 | **3,734,296** | 284,820 | 17287.4 (Py) |
| `pair-byte` (pair) | 8,147 | 56,939 | 33,238 | -41.6% | 3,922,728 | **3,733,120** | 276,254 | 16009.3 (Py) |
| `bpe` (pair) | 8,147 | 71,823 | 33,238 | -53.7% | 3,976,568 | **3,667,888** | 285,861 | 15293.8 (Py) |
| zstd-19 lean (8K primary dict) | n/a | 8,192 | 8,192 | 0.0% | 1,882,328 | **1,882,328** | n/a | 15.9 (C) |
| zstd-19 lean (32K primary dict) | n/a | 32,768 | 32,768 | 0.0% | 2,066,800 | **2,066,800** | n/a | 13.9 (C) |
| zstd-19 lean (no dict) | n/a | 0 | 0 | 0.0% | 1,856,360 | **1,856,360** | n/a | 15.9 (C) |

- Honest `zstd-19` comparator note: `exact-closed (A1AD)` vs `zstd-19 lean (8K dict)` status = `b_dominates` (M* = `None` B); `zstd-19` remains strictly smaller in complete bits on these fresh corpora.

## All 4 Preregistered Budgets Summary (`A1AD` Complete Bits / Min-DP Tokens)

| Budget | Arm | Frags | `A1AF` -> `A1AD` Hdr (B) | `fresh-js-24repos` `A1AD` Bits (Min-DP Tok) | `fresh-py-12repos` `A1AD` Bits (Min-DP Tok) |
| --- | --- | ---: | --- | ---: | ---: |
| `dag_header_small` | `open` | 84 | 1,171 -> 878 (-25.0%) | 5,710,232 (851,068) | 3,640,144 (566,304) |
| `dag_header_small` | `open-byte` | 128 | 1,171 -> 873 (-25.4%) | 5,665,624 (769,473) | 3,586,896 (504,218) |
| `dag_header_small` | `exact-closed` | 168 | 1,408 -> 878 (-37.6%) | 5,589,280 (753,001) | 3,535,904 (491,616) |
| `dag_header_small` | `pair-byte` | 168 | 1,293 -> 878 (-32.1%) | 5,669,512 (749,660) | 3,576,056 (488,918) |
| `dag_header_small` | `bpe` | 168 | 1,413 -> 878 (-37.9%) | 5,575,024 (749,745) | 3,540,688 (490,056) |
| `dag_header_large` | `open` | 3,924 | 47,925 -> 33,241 (-30.6%) | 6,174,824 (567,111) | 4,086,616 (370,608) |
| `dag_header_large` | `open-byte` | 6,314 | 50,912 -> 33,240 (-34.7%) | 6,023,824 (467,133) | 3,927,776 (298,161) |
| `dag_header_large` | `exact-closed` | 8,147 | 67,963 -> 33,238 (-51.1%) | 5,642,152 (443,280) | 3,734,296 (284,820) |
| `dag_header_large` | `pair-byte` | 8,147 | 56,939 -> 33,238 (-41.6%) | 5,697,800 (430,831) | 3,733,120 (276,254) |
| `dag_header_large` | `bpe` | 8,147 | 71,823 -> 33,238 (-53.7%) | 5,538,424 (443,986) | 3,667,888 (285,861) |
| `slots_small` | `open` | 84 | 1,171 -> 878 (-25.0%) | 5,710,232 (851,068) | 3,640,144 (566,304) |
| `slots_small` | `open-byte` | 84 | 953 -> 700 (-26.6%) | 5,731,984 (815,258) | 3,618,744 (536,567) |
| `slots_small` | `exact-closed` | 84 | 944 -> 605 (-35.9%) | 5,702,360 (819,285) | 3,556,736 (527,437) |
| `slots_small` | `pair-byte` | 84 | 893 -> 605 (-32.2%) | 5,816,144 (822,356) | 3,600,680 (525,435) |
| `slots_small` | `bpe` | 84 | 944 -> 605 (-35.9%) | 5,675,536 (818,429) | 3,528,600 (522,475) |
| `slots_large` | `open` | 3,924 | 47,925 -> 33,241 (-30.6%) | 6,174,824 (567,111) | 4,086,616 (370,608) |
| `slots_large` | `open-byte` | 3,924 | 27,963 -> 18,691 (-33.2%) | 5,594,208 (476,095) | 3,631,680 (305,499) |
| `slots_large` | `exact-closed` | 3,924 | 30,925 -> 15,259 (-50.7%) | 5,316,088 (468,981) | 3,476,624 (301,688) |
| `slots_large` | `pair-byte` | 3,924 | 25,163 -> 15,259 (-39.4%) | 5,383,168 (456,039) | 3,487,600 (293,178) |
| `slots_large` | `bpe` | 3,924 | 31,493 -> 15,259 (-51.5%) | 5,294,992 (473,782) | 3,471,976 (305,759) |

## Live Pinned `tiktoken` Reachability & Native Encoder Inflation on Fresh Corpora

`tiktoken` applies an O(1) whole-piece hash shortcut when a regex match equals a single vocab key (`isolated_shadowed = 0`), but runs `byte_pair_encode` inside real documents (`embedded_shadowed`), where live `tiktoken==0.14.0` matches `validate_encoders.py` with **0 discrepancies** (`0` for `bpe`, `852 / 8,036` for `exact-closed`) and **0 token-stream parity mismatches across all 476/476 fresh files**.

| Model (frozen `primary` @ `dag_header_large`) | Live `tiktoken` Embedded Shadowed | Pure-Python Shadowed | JS UTF-8 RT & Parity | JS Native Tokens (vs Min-DP) | Py UTF-8 RT & Parity | Py Native Tokens (vs Min-DP) |
| --- | ---: | ---: | --- | ---: | --- | ---: |
| `bpe-dag-large` | 0 / 7991 | 0 (full=0) | 345/345 (0 diff) | 459,301 (+3.45%) | 131/131 (0 diff) | 296,765 (+3.81%) |
| `exact-closed-dag-large` | 852 / 8036 | 852 (full=853) | 345/345 (0 diff) | 482,003 (+8.74%) | 131/131 (0 diff) | 307,019 (+7.79%) |

## Native HF `tokenizers` BPE & `sentencepiece` Unigram Controls (Fresh Corpora)

| Native Control (Primary-Trained) | Frags | `A1AD` Hdr (B) | JS Min-DP Tok | JS Native Tok (Inflation) | Py Min-DP Tok | Py Native Tok (Inflation) | UTF-8 RT |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `hf-bytelevel-bpe-340` | 84 | 605 | 825,658 | 837,758 (+1.47%) | 528,287 | 538,215 (+1.88%) | PASS |
| `hf-bytelevel-bpe-4180` | 3,205 | 12,383 | 493,851 | 505,926 (+2.45%) | 307,816 | 317,539 (+3.16%) | PASS |
| `hf-bytelevel-bpe-7756` | 3,205 | 12,383 | 493,851 | 505,926 (+2.45%) | 307,816 | 317,539 (+3.16%) | PASS |
| `sp-unigram-4280` | 3,936 | 29,544 | 701,338 | 711,703 (+1.48%) | 482,840 | 489,943 (+1.47%) | PASS |
| `sp-unigram-440` | 107 | 962 | 951,631 | 951,785 (+0.02%) | 692,177 | 692,177 (+0.00%) | PASS |
| `sp-unigram-600` | 267 | 2,004 | 897,216 | 900,293 (+0.34%) | 646,966 | 649,007 (+0.32%) | PASS |
| `sp-unigram-6500` | 6,156 | 43,769 | 640,579 | 649,853 (+1.45%) | 443,948 | 452,790 (+1.99%) | PASS |
| `sp-unigram-8500` | 8,156 | 54,398 | 596,612 | 608,158 (+1.94%) | 415,066 | 424,910 (+2.37%) | PASS |

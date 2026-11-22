# Phase 4 Lossless Encoding & Press-Count Bake-Off (21 Frozen Real Code Corpora)

Strictly separate from capacity certification. Every file in every regime passed independent round-trip UTF-8 byte decode verification (`decode(encode(s)) == s`). **Press counts measure token/key operations only and do NOT claim human typing speed.**

## 1. Per-Corpus Results (`presses` | `payload + dict = total bytes`)

| ID | Lang | `|Sigma|` | Raw B | `K=64` | 6-bit No-Esc (`p` / `tot B`) | 6-bit+Esc (`p` / `tot B` / `esc B`) | 7-bit 128 (`p` / `tot B`) | 8-bit 256 (`p` / `tot B`) | Best Total B | Best Presses |
| --- | --- | ---: | ---: | --- | --- | --- | --- | --- | --- | --- |
| IND-JS-1 | js | 59 | 3133 | `FEASIBLE` | 2682 / 2191 | 2739 / 2229 / 0 | 1658 / 2064 | 1525 / 2325 | `7b-128` | `8b-256` |
| IND-JS-2 | js | 75 | 7606 | `IMPOSSIBLE` | N/A | 6035 / 4707 / 90 | 3917 / 3960 | 3335 / 4394 | `7b-128` | `8b-256` |
| IND-JS-3 | js | 90 | 18645 | `IMPOSSIBLE` | N/A | 17134 / 13114 / 464 | 13559 / 12244 | 10757 / 11898 | `8b-256` | `8b-256` |
| IND-PY-1 | python | 61 | 5128 | `FEASIBLE` | 4223 / 3313 | 4318 / 3375 / 0 | 2627 / 3137 | 2411 / 3472 | `7b-128` | `8b-256` |
| IND-PY-2 | python | 76 | 15208 | `IMPOSSIBLE` | N/A | 12626 / 9662 / 133 | 9155 / 8434 | 7123 / 8366 | `8b-256` | `8b-256` |
| IND-PY-3 | python | 86 | 27129 | `IMPOSSIBLE` | N/A | 19328 / 14882 / 213 | 14125 / 12933 | 12415 / 14152 | `7b-128` | `8b-256` |
| IND-C-1 | c | 64 | 3714 | `FEASIBLE` | 3714 / 2916 | 2624 / 2211 / 19 | 1581 / 2025 | 1504 / 2244 | `7b-128` | `8b-256` |
| IND-C-2 | c | 67 | 7638 | `IMPOSSIBLE` | N/A | 5302 / 4192 / 56 | 3414 / 3667 | 3179 / 4292 | `7b-128` | `8b-256` |
| IND-C-3 | c | 85 | 13426 | `IMPOSSIBLE` | N/A | 11924 / 9191 / 374 | 8173 / 7590 | 5820 / 7376 | `8b-256` | `8b-256` |
| RACE-B01 | Python | 58 | 3657 | `FEASIBLE` | 2541 / 2123 | 2626 / 2180 / 0 | 1604 / 2018 | 1512 / 2298 | `7b-128` | `8b-256` |
| RACE-B02 | Zig | 59 | 3664 | `FEASIBLE` | 2847 / 2291 | 2979 / 2385 / 0 | 1512 / 1874 | 1363 / 2218 | `7b-128` | `8b-256` |
| RACE-B03 | WGSL | 64 | 2237 | `FEASIBLE` | 2237 / 1808 | 1156 / 1389 / 17 | 1139 / 1541 | 1139 / 1683 | `6b+esc` | `7b-128` |
| RACE-B04 | WGSL | 65 | 5976 | `FEASIBLE` | 4541 / 3725 | 4474 / 3687 / 55 | 2235 / 4364 | 2085 / 4680 | `6b+esc` | `8b-256` |
| RACE-B05 | JavaScript | 66 | 1797 | `IMPOSSIBLE` | N/A | 1570 / 1333 / 17 | 1048 / 1312 | 1026 / 1435 | `7b-128` | `8b-256` |
| RACE-B06 | Python | 67 | 8255 | `IMPOSSIBLE` | N/A | 6592 / 5118 / 25 | 4822 / 4669 | 4214 / 5221 | `7b-128` | `8b-256` |
| RACE-B07 | C | 68 | 3308 | `IMPOSSIBLE` | N/A | 1945 / 1823 / 31 | 1200 / 1748 | 1193 / 1961 | `7b-128` | `8b-256` |
| RACE-B08 | Python | 69 | 5248 | `IMPOSSIBLE` | N/A | 4171 / 3443 / 40 | 2587 / 3067 | 2076 / 3308 | `7b-128` | `8b-256` |
| RACE-B09 | JavaScript | 70 | 5204 | `IMPOSSIBLE` | N/A | 4377 / 3449 / 42 | 3098 / 3149 | 2520 / 3432 | `7b-128` | `8b-256` |
| RACE-B10 | C | 71 | 6434 | `IMPOSSIBLE` | N/A | 4529 / 3795 / 39 | 2924 / 3314 | 2704 / 3852 | `7b-128` | `8b-256` |
| RACE-B11 | WGSL | 73 | 9186 | `FEASIBLE` | 7602 / 5870 | 6416 / 5257 / 121 | 4469 / 8080 | 4242 / 12845 | `6b+esc` | `8b-256` |
| RACE-B12 | JavaScript | 74 | 4167 | `IMPOSSIBLE` | N/A | 3702 / 2939 / 43 | 2747 / 2787 | 2319 / 3004 | `7b-128` | `8b-256` |

## 2. Honest Summary

- **Total corpora evaluated:** `21` (`8` certified `FEASIBLE` at `K=64` without escapes, `13` `IMPOSSIBLE`).
- **Best total lossless package bytes (`payload + dict`) across all 21 corpora:** `{'7b-128': 15, '8b-256': 3, '6b+esc': 3}`.
- **Fewest presses across all 21 corpora:** `{'8b-256': 20, '7b-128': 1}`.
- **On the `8` `K=64` `FEASIBLE` corpora:**
  - `6-bit no-escape` beat `6-bit + escape` on total bytes in `4/8` corpora.
  - `6-bit no-escape` beat `7-bit (128)` on total bytes in `2/8` corpora (and on payload bytes alone in `0/8`).
- **Elapsed wall time:** `60.3 s`.


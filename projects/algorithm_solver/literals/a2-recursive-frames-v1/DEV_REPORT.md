# BITS Experiment Card A2 — Recursive Frames for Normalized JavaScript (Dev Report)

## Executive Summary & Honest Verdict

- **Recursive-Frame Grammar Iteration Status:** **`CLOSED`** (`D=3` vs `D=1` achieved `-0.11%` complete bits against the `1.0%` bar -> `FAIL`; not carried forward to sealed fresh code).
- **Depth-1 Preregistration Status:** **`PREREGISTERED`** — Depth-1 Frames (`Arm 3`) vs Context AST (`Arm 2`) achieved `-6.14%` (`95% CI [-11.34%, -3.25%]`) on dev and is preregistered for head-to-head sealed fresh-code evaluation in [`PREREGISTRATION_DEPTH1.md`](PREREGISTRATION_DEPTH1.md).
- **Corpus:** Strictly spent local JS sources only, lineage-disjoint split (`762` train files across `527` lineages; `540` dev files across `421` lineages; `0` shared lineages, `0` shared problem IDs, `0` IBM cluster leaks, `0` cross-split duplicates).
- **Normalization & AST Coverage:** `540/540` (`0.0%` fallback rate); `100.0%` byte-for-byte independent decode across all 4 arms; `20/20` frozen Node behavior programs (`3834/3834` test cases) passed across all 4 arms.
- **Arm 2 (Context AST) vs Arm 1 (Flat BITS):** `-33.27%` complete bits (`-447,664` bits).
- **Arm 3 (Depth-1 Frames, D=1) vs Arm 2 (Context AST):** `-6.14%` complete bits (`-55,104` bits; 95% lineage CI `[-11.34%, -3.25%]`).
- **Arm 4 (Recursive Frames, D=3) vs Arm 2 (Context AST):** `-6.24%` complete bits (`-56,032` bits; 95% lineage CI `[-11.54%, -3.31%]`).
- **Decisive Recursive vs Depth-1 Comparison (Arm 4 vs Arm 3):** `-0.11%` complete bits (`-928` bits; paired 95% CI at lineage unit `[-0.25%, -0.05%]`; lineages improved/tied/worse = `239/0/182`).
- **1% Target Check (Arm 4 beats Arm 3 by >= 1.0% complete bits):** point estimate = `FAIL (gain < 1.0%)`, 95% CI upper bound = `FAIL`.

## Primary Horizon Complete-Bit Table (540 Dev Files, 421 Lineages, 371,778 Normalized Bytes)

| Arm | Complete Bits | Header Bits | Payload Bits | Bits / Norm Byte | Delta vs Arm 1 | Delta vs Arm 2 | Delta vs Arm 3 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Arm 1 — Flat BITS | 1,345,672 | 20,632 | 1,325,024 | 3.6196 | +0.00% | +49.85% | +59.65% |
| Arm 2 — Context AST (D=0) | 898,008 | 46,848 | 851,144 | 2.4154 | -33.27% | +0.00% | +6.54% |
| Arm 3 — Depth-1 Frames (D=1) | 842,904 | 55,320 | 787,568 | 2.2672 | -37.36% | -6.14% | +0.00% |
| Arm 4 — Recursive Frames (D=3) | 841,976 | 54,640 | 787,320 | 2.2647 | -37.43% | -6.24% | -0.11% |

## Frame Diagnostics (Exact 8-Cyclic-Register-Shift Enumeration, No FFT/NTT)

| Arm | Total Frames | Nested Defs (D>=2) | Depth Hist | Frame Uses | Actual Nested Calls | Def Header Bytes | Switch Bits | Frame-ID Bits | Shift Bits | Body Savings vs Arm 2 (bits) |
| --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Arm 2 — Context AST (D=0) | 0 | 0 | `{}` | 0 | 0 | 0 | 0.0 | 0.0 | 0.0 | +0.0 |
| Arm 3 — Depth-1 Frames (D=1) | 188 | 0 | `{"1": 188}` | 6,874 | 0 | 852 | 21,357.7 | 40,464.5 | 8,835.2 | +134,233.3 |
| Arm 4 — Recursive Frames (D=3) | 215 | 111 | `{"1": 104, "2": 72, "3": 39}` | 6,733 | 4,949 | 739 | 21,085.4 | 39,724.1 | 8,729.9 | +133,363.4 |

## Header-Repayment Break-Even Horizon (M*)

| Comparison | Delta Header Bits | Dev Payload Saving Bits | Status | M* (Norm Bytes) | M* (Files) | M* (Lineages) |
| --- | ---: | ---: | --- | ---: | ---: | ---: |
| `arm2_vs_arm1` | +26,216 | +473,880 | `repaid_within_dev` | 20,567.5 | 29.87 | 23.29 |
| `arm3_vs_arm2` | +8,472 | +63,576 | `repaid_within_dev` | 49,542.3 | 71.96 | 56.10 |
| `arm4_vs_arm2` | +7,792 | +63,824 | `repaid_within_dev` | 45,388.8 | 65.93 | 51.40 |
| `arm4_vs_arm3` | -680 | +248 | `immediate_win_header_and_payload` | 0.0 | 0.00 | 0.00 |

## Volume Sweep (Prefix Archives by Lineage Count)

| Lineages | Files | Norm Bytes | Arm 1 Bits | Arm 2 Bits | Arm 3 Bits | Arm 4 Bits | Arm 3 vs 2 | Arm 4 vs 2 | Arm 4 vs 3 |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 10 | 10 | 6,421 | 40,335 | 58,408 | 64,567 | 63,871 | +10.54% | +9.35% | -1.08% |
| 25 | 144 | 136,926 | 604,807 | 471,549 | 473,631 | 472,847 | +0.44% | +0.28% | -0.17% |
| 50 | 169 | 155,874 | 666,231 | 507,384 | 504,365 | 503,519 | -0.59% | -0.76% | -0.17% |
| 100 | 219 | 185,361 | 759,177 | 559,715 | 549,226 | 548,311 | -1.87% | -2.04% | -0.17% |
| 200 | 319 | 241,212 | 936,078 | 661,922 | 637,988 | 637,067 | -3.62% | -3.75% | -0.14% |
| 300 | 419 | 302,324 | 1,124,810 | 771,036 | 731,975 | 730,978 | -5.07% | -5.20% | -0.14% |
| 421 | 540 | 371,778 | 1,345,672 | 898,008 | 842,904 | 841,976 | -6.14% | -6.24% | -0.11% |

## Per-Slice Lineage-Disjoint Breakdown

| Dev Slice | Files | Lineages | Norm Bytes | Arm 2 Payload | Arm 3 Payload | Arm 4 Payload | Arm 3 vs 2 Pay | Arm 4 vs 3 Pay | Arm 4 vs 3 Complete |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `codenet-fresh` | 200 | 200 | 129,394 | 234,632 | 201,472 | 201,312 | -14.13% | -0.08% | -0.33% |
| `codenet-fresh2` | 200 | 200 | 115,895 | 209,896 | 181,720 | 181,696 | -13.42% | -0.01% | -0.30% |
| `sources-20` | 20 | 20 | 5,513 | 11,264 | 10,736 | 10,720 | -4.69% | -0.15% | -1.05% |
| `express` | 120 | 1 | 120,976 | 395,368 | 393,656 | 393,608 | -0.43% | -0.01% | -0.16% |

- **420 Balanced Single-Problem Algorithm Lineages (`codenet-fresh` + `codenet-fresh2` + `sources-20`, excluding multi-file `repo:express`):** Arm 3 vs Arm 2 = `-10.62%`, Arm 4 vs Arm 2 = `-10.80%`, Arm 4 vs Arm 3 = `-0.19%` (95% lineage CI `[-0.27%, -0.12%]`, improved/tied/worse = `238/0/182`).

## Measured Work (`shared_spine.measured_work`)

- **Platform:** `macOS-26.6.2-arm64-arm-64bit-Mach-O`, Python `3.14.2`, Node `v22.20.0`
- **Peak RSS:** `468.48 MB`
- **Normalization wall-clock:** train `0.621s`, dev `0.569s`
- **Behavior verification wall-clock (all 4 arms x 3,834 cases):** `0.537s`

| Arm | Train (s) | Encode Dev (s) | Indep Decode Dev (s) | Decode p95 (ms/file) | Shift Evals (Train+Dev) | DP Nodes / Bytes | AC32 Symbols (Dev) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Arm 1 — Flat BITS | 42.203 | 1.511 | 0.986 | 5.900 | 0 | 2,058,682 | 164,193 |
| Arm 2 — Context AST (D=0) | 0.068 | 1.272 | 1.178 | 5.930 | 0 | 99,006 | 306,165 |
| Arm 3 — Depth-1 Frames (D=1) | 32.597 | 3.728 | 1.252 | 5.964 | 66,990,979 | 1,536,474 | 260,562 |
| Arm 4 — Recursive Frames (D=3) | 51.675 | 4.019 | 1.322 | 5.792 | 72,719,265 | 1,536,474 | 260,653 |

## Scientific Interpretation & Decisions

- **Recursive-Frame Grammar Iteration — CLOSED (`FAIL` vs 1.0% bar):** Arm 4 (`D_max=3`) genuinely learns nested frame definitions (`def_depth` 2 and 3) with composed mod-8 shifts, saving `-13.3%` in definition header bytes (`-680` total header bits, `M* = 0`) and `-248` payload bits (`-0.11%` complete bits total, 95% CI `[-0.25%, -0.05%]`). Because a fair uncrippled Arm 3 already supports `<H>` holes and flattened compound templates, recursive frame definitions fall far short of the `1.0%` complete-bit promotion bar. This iteration is **CLOSED** and recorded as a negative result for recursion.
- **Depth-1 Frames (`Arm 3`) vs Context-Coded AST (`Arm 2`) — PREREGISTERED:** Across 421 unseen JS lineages, Depth-1 frames with exact 8-cyclic-register-shift enumeration (`0..7`, zero FFT/NTT) beat the strong Binary-AST context model by **`-6.14%`** complete bits (`95% CI [-11.34%, -3.25%]`) even after charging every frame definition, switch, frame ID, and cyclic shift bit. A head-to-head sealed fresh-code evaluation comparing frozen Arm 3 vs frozen Arm 2 is preregistered in [`PREREGISTRATION_DEPTH1.md`](PREREGISTRATION_DEPTH1.md).

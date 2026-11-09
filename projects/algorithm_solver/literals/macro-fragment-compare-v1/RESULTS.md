# Matched macro / fragment comparison

This measures encoding of existing qualified solutions, not finding solutions from problem descriptions. All primary-language packets independently reconstruct the exact receipt-bound source bytes. The 300-fit/100-development-validation partition was reused; validation is exposed development, not fresh confirmation.

Dictionary search is heuristic. It does not establish the globally best 64/128/256-entry language. The mixed arm is a lossless AST-derived source macro DSL with charged operands, not a complete typed semantic compiler.

Payload word-equivalents below are total payload bits divided by width. They include spelling and operands; they are not opcode counts. Packets additionally charge nine framing bytes and byte padding.

## Exposed development validation

| Language | Width | Representation | Exact-source coverage | Mean words-equivalent | p50 | p95 | Without spelling |
|---|---:|---|---:|---:|---:|---:|---:|
| javascript | 6 | Counted fragments | 100/100 | 235.38 | 176.67 | 514.50 | 0 |
| javascript | 6 | Prefix literal control | 100/100 | 236.44 | 176.75 | 523.17 | 0 |
| javascript | 6 | Mixed fixed-arity macros | 100/100 | 236.49 | 176.75 | 524.50 | 0 |
| javascript | 7 | Counted fragments | 100/100 | 189.15 | 142.64 | 412.14 | 0 |
| javascript | 7 | Prefix literal control | 100/100 | 189.52 | 143.36 | 412.14 | 0 |
| javascript | 7 | Mixed fixed-arity macros | 100/100 | 185.61 | 142.36 | 385.43 | 0 |
| javascript | 8 | Counted fragments | 100/100 | 156.77 | 120.12 | 337.62 | 0 |
| javascript | 8 | Prefix literal control | 100/100 | 156.80 | 120.12 | 337.62 | 0 |
| javascript | 8 | Mixed fixed-arity macros | 100/100 | 153.09 | 116.62 | 313.38 | 0 |
| python | 6 | Counted fragments | 100/100 | 540.39 | 431.75 | 1139.83 | 0 |
| python | 6 | Prefix literal control | 100/100 | 540.39 | 431.75 | 1139.83 | 0 |
| python | 6 | Mixed fixed-arity macros | 100/100 | 540.39 | 431.75 | 1139.83 | 0 |
| python | 7 | Counted fragments | 100/100 | 428.20 | 361.14 | 866.00 | 0 |
| python | 7 | Prefix literal control | 100/100 | 428.20 | 361.14 | 866.00 | 0 |
| python | 7 | Mixed fixed-arity macros | 100/100 | 427.96 | 361.14 | 866.00 | 0 |
| python | 8 | Counted fragments | 100/100 | 336.96 | 273.62 | 708.75 | 0 |
| python | 8 | Prefix literal control | 100/100 | 336.96 | 273.62 | 708.75 | 0 |
| python | 8 | Mixed fixed-arity macros | 100/100 | 336.50 | 273.62 | 708.75 | 0 |

The prefix literal control reserves the same CONCAT code as the mixed arm. Compare mixed versus that control to isolate the learned macros; compare mixed versus counted fragments for the complete protocol tradeoff.

## Paired changes on the same validation problems

| Language | Width | Mixed vs counted-fragment bits | Better / equal / worse | Mixed vs prefix-control bits |
|---|---:|---:|---:|---:|
| javascript | 6 | +0.47% | 25 / 55 / 20 | +0.02% |
| javascript | 7 | -1.87% | 54 / 39 / 7 | -2.06% |
| javascript | 8 | -2.35% | 49 / 44 / 7 | -2.37% |
| python | 6 | +0.00% | 0 / 100 / 0 | +0.00% |
| python | 7 | -0.05% | 38 / 61 / 1 | -0.05% |
| python | 8 | -0.14% | 23 / 77 / 0 | -0.14% |

## Complete packet costs and selection accounting

Every packet includes nine framing bytes and byte padding. Primary selections are opcode dispatches; count words and spelling payload are charged separately. These means all use the same 100 validation sources.

| Language | Width | Representation | Mean packet words-equivalent | Packet p50 | Packet p95 | Mean primary selections | Mean count words | Mean spelling bits | Mean closing bits |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|
| javascript | 6 | Counted fragments | 247.96 | 189.33 | 526.67 | 65.12 | 0.00 | 994.95 | 26.59 |
| javascript | 6 | Prefix literal control | 249.04 | 189.33 | 536.00 | 64.92 | 0.00 | 1002.51 | 26.60 |
| javascript | 6 | Mixed fixed-arity macros | 249.07 | 189.33 | 537.33 | 62.60 | 1.23 | 1010.43 | 25.52 |
| javascript | 7 | Counted fragments | 199.94 | 153.71 | 422.86 | 70.07 | 0.00 | 806.67 | 26.90 |
| javascript | 7 | Prefix literal control | 200.30 | 154.29 | 422.86 | 69.99 | 0.00 | 809.82 | 26.89 |
| javascript | 7 | Mixed fixed-arity macros | 196.40 | 153.14 | 396.57 | 68.10 | 1.53 | 785.88 | 26.00 |
| javascript | 8 | Counted fragments | 166.23 | 129.50 | 347.00 | 68.76 | 0.00 | 679.23 | 24.86 |
| javascript | 8 | Prefix literal control | 166.25 | 129.50 | 347.00 | 68.61 | 0.00 | 680.76 | 24.75 |
| javascript | 8 | Mixed fixed-arity macros | 162.53 | 126.00 | 323.00 | 66.13 | 1.12 | 663.30 | 23.42 |
| python | 6 | Counted fragments | 552.95 | 444.00 | 1152.00 | 57.91 | 0.00 | 2867.13 | 27.73 |
| python | 6 | Prefix literal control | 552.95 | 444.00 | 1152.00 | 57.91 | 0.00 | 2867.13 | 27.73 |
| python | 6 | Mixed fixed-arity macros | 552.95 | 444.00 | 1152.00 | 57.91 | 0.00 | 2867.13 | 27.73 |
| python | 7 | Counted fragments | 438.94 | 372.00 | 876.57 | 63.46 | 0.00 | 2523.51 | 29.64 |
| python | 7 | Prefix literal control | 438.94 | 372.00 | 876.57 | 63.46 | 0.00 | 2523.51 | 29.64 |
| python | 7 | Mixed fixed-arity macros | 438.72 | 372.00 | 876.57 | 63.75 | 0.00 | 2519.55 | 29.95 |
| python | 8 | Counted fragments | 346.42 | 283.00 | 718.00 | 75.81 | 0.00 | 2054.97 | 34.23 |
| python | 8 | Prefix literal control | 346.42 | 283.00 | 718.00 | 75.79 | 0.00 | 2055.15 | 34.21 |
| python | 8 | Mixed fixed-arity macros | 345.93 | 283.00 | 718.00 | 75.69 | 0.00 | 2052.36 | 34.14 |

## Static compact-Python diagnostic

Fit dictionaries were sealed before validation transformation. Unsupported transforms retain original source bytes in the full denominator. These successor sources have no fresh native qualification: the table is a static representation measurement, not newly qualified coverage.

| Width | Representation | Full validation intersection | Mean payload words-equivalent | p50 | p95 | Transformed-only n / mean / p50 / p95 |
|---|---|---:|---:|---:|---:|---|
| 6 | Counted fragments | 100/100 | 238.31 | 186.25 | 533.83 | 100 / 238.31 / 186.25 / 533.83 |
| 6 | Prefix literal control | 100/100 | 238.31 | 186.25 | 533.83 | 100 / 238.31 / 186.25 / 533.83 |
| 6 | Mixed fixed-arity macros | 100/100 | 238.31 | 186.25 | 533.83 | 100 / 238.31 / 186.25 / 533.83 |
| 7 | Counted fragments | 100/100 | 193.14 | 151.07 | 412.00 | 100 / 193.14 / 151.07 / 412.00 |
| 7 | Prefix literal control | 100/100 | 193.14 | 151.07 | 412.00 | 100 / 193.14 / 151.07 / 412.00 |
| 7 | Mixed fixed-arity macros | 100/100 | 192.37 | 151.07 | 409.86 | 100 / 192.37 / 151.07 / 409.86 |
| 8 | Counted fragments | 100/100 | 151.12 | 115.12 | 321.88 | 100 / 151.12 / 115.12 / 321.88 |
| 8 | Prefix literal control | 100/100 | 151.21 | 115.12 | 321.88 | 100 / 151.21 / 115.12 / 321.88 |
| 8 | Mixed fixed-arity macros | 100/100 | 149.48 | 115.12 | 313.38 | 100 / 149.48 / 115.12 / 313.38 |

Validation transformer: 100 transformed; 0 original fallbacks. Freshly qualified successors: 0.

## Reproduction and limits

- [Counting contract](CONTRACT.md); [machine-readable results](results.json).
- `run.py` requires the existing hash-pinned KnownSpecService configuration and an out-of-repository private output directory. It refuses source outside the guarded service.
- Private source files, dictionaries and packets are retained outside Git. Public results bind their source, receipt, table and packet hashes.
- `test_codec.py` checks exhaustive short-string optimal segmentation, nested macro operands, exact integer/Unicode bytes, malformed packets, ownership and AST spans.
- The prerequisite lane checks passed; 27 native judge tests were skipped because this host lacks bubblewrap/prlimit. No candidate was executed without the required sandbox.
- No protected source, model call, training, publication, new native qualification, autonomous solving, or human-fluency result is claimed.
- Whole fit sources/function units/bodies are excluded as table entries. Literals and macro shells must recur in at least two distinct fitting source hashes. Spelling remains an explicit general fallback.
- Decoder and dictionary byte sizes, source membership failures, packet overheads and every fit trial are retained in results.json.

Measured process elapsed: 223.712 seconds. Runtime: darwin. Results SHA-256: `361ebafaa749f8d70da9df773ab41438a69039c57d774e47bf05db22f1d44d7e`.

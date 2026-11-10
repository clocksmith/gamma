# Pure literal development result

Pure 7/8-bit dictionaries reconstruct **all 400 known development programs in each language**,
including all 100 exposed validation programs. This is exact representation of qualified
source, not solving from statements, new native qualification, or 1,000 problems.

Each selected code inserts only its stored string. At 7 bits the selected tables contain
98 ordinary ASCII characters and 30 flat merged strings; at 8 bits, 98 characters and
158 merged strings. No spelling mode, macro, free binding or hidden helper exists.
These are compression-first fragments, not a human-tested idiom vocabulary.
Six-bit fitting selects 64 ordinary characters and retains partial coverage.

## Exposed validation, 100 original IDs per language

| Language | Width | Complete | Median selections | p95 | Singleton bits | Dictionary bytes | Packets bytes |
|---|---:|---:|---:|---:|---:|---:|---:|
| javascript | 6 | 71/100 | 192 | 508 | 100.00% | 328 | 14547 |
| javascript | 7 | 100/100 | 139 | 389 | 81.52% | 708 | 20446 |
| javascript | 8 | 100/100 | 89.5 | 286 | 60.04% | 1690 | 16406 |
| python | 6 | 82/100 | 345 | 850 | 100.00% | 328 | 28882 |
| python | 7 | 100/100 | 245.5 | 609 | 79.75% | 709 | 30672 |
| python | 8 | 100/100 | 163.5 | 403 | 53.90% | 1677 | 24490 |

Conditional costs for incomplete six-bit rows are not complete-population wins.
The 7/8-bit tables cover every fitting source and every validation source.

## Matched 8-bit comparison with the previous mixed macro/spelling protocol

Every compared source hash matches the earlier measurement. Both arms cover all 100
validation sources. Pure literal selections are compared with fully charged mixed
payload word-equivalents, not just the mixed opcode count.

| Language | Pure median | Mixed median words | Payload change | Complete packet change |
|---|---:|---:|---:|---:|
| javascript | 89.5 | 116.625 | -19.62% | +0.94% |
| python | 163.5 | 273.625 | -39.41% | -29.21% |

The existing pure-literal format has **41 header bytes**, versus **9** for the
mixed protocol. That real 32-byte difference makes JavaScript pure packets slightly
larger despite lower input bits. Do not describe it as a complete-packet JavaScript win.
Stored dictionary-plus-100-packet packages are 18,096 versus 22,070 bytes for JavaScript,
and 26,167 versus 40,814 for Python. These use their implemented binary versus JSON
dictionary formats; they do not isolate an intrinsic dictionary-storage advantage.
The pure decoder source closure is 13,014 bytes, counted separately
from dictionaries and packets; the mixed decoder reports 9,418 bytes.
Including those decoder source files gives 31,110 versus 31,488 bytes for JavaScript
and 39,181 versus 50,232 for Python, across each 100-program package.
Neither count includes the language interpreter/standard library.

## Preserved failures and scope

The original fit-observed-alphabet run covered only 99/100 JavaScript and 98/100
Python validation sources at 7/8 bits. Its result and packets remain preserved.
The fixed ASCII continuation was motivated by that development failure. It fits only
the 300 fitting sources, but the validation population was already exposed and is
not an untouched confirmation set. The initial pre-validation attempt was stopped
after identifying redundant work; identical alphabet caching and length-indexed
exclusions preserve candidate selection. No validation source was read in that attempt.

This does not beat the historical jointly rewritten 8-bit literal frontier of 8,283
validation selections, median 61.5, p95 195 and about 49.5% singleton bits: that used
different source alternatives. The present exact-source arm has 12,306 JavaScript
selections. Neither satisfies M1 median <=32, p95 <=96 or <=10% singleton bits.
No globally optimal vocabulary, unfamiliar-family success or human usability claim.

## Evidence and reproduction

- [Initial contract](CONTRACT.md), [ASCII continuation](ASCII-CONTINUATION.md).
- [Initial source-free results](results.json), [continuation results](ascii-results.json).
- [Matched comparisons](comparison.json), [initial replay](verification.json), [ASCII replay](ascii-verification.json).
- `test_core.py` and `test_verify.py`: 15 focused tests, including brute-force short
  segmentation, malformed packets and fail-closed population/width checks.
- 45 KnownSpecService/boundary tests passed. Existing pytest judge/lane tests could
  not start because pytest is not installed; no native execution is claimed.
- Exact private tables and packed source are not redistributed. Public reports retain
  original source/receipt identities, table hashes, every arm score and merge trace.

Run from Gamma with an explicitly authorized pinned KnownSpecService configuration.
Each output directory must be new and outside Git:

```sh
python3 projects/algorithm_solver/literals/pure-literal-compare-v1/test_core.py
python3 projects/algorithm_solver/literals/pure-literal-compare-v1/test_verify.py
python3 projects/algorithm_solver/literals/pure-literal-compare-v1/run.py --service "$CONFIG" --service-sha256 "$SHA" --output "$PRIVATE_INITIAL" --report "$INITIAL_REPORT"
python3 projects/algorithm_solver/literals/pure-literal-compare-v1/ascii_run.py --service "$CONFIG" --service-sha256 "$SHA" --previous "$PRIVATE_INITIAL" --output "$PRIVATE_ASCII" --report "$ASCII_REPORT"
python3 projects/algorithm_solver/literals/pure-literal-compare-v1/verify.py --private "$PRIVATE_ASCII" --output "$VERIFICATION"
python3 projects/algorithm_solver/literals/pure-literal-compare-v1/report.py
```

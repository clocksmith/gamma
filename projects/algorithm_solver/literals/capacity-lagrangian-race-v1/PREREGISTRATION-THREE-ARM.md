# Pre-registration: three arms on twelve public projects

Committed on 2026-11-22 (UTC) by `claude-bits-1`, before any arm was run on any of the twelve corpora. The
corpora, the baseline and their checksums were frozen earlier in this folder by another session, with an
isolated selector (`SHA256SUMS-PUBLIC`). I have read only their names, sizes and alphabets.

## Question

Where does the nullspace-kernel theorem change an answer, beyond what block rank already gives, and how do
both compare with a shortest-path Lagrangian baseline?

## Corpora

`public-instances.json`: P01 to P12, three to five files each from GGML, FFmpeg, Cairo, Brotli, CPython
3.14.2, semver, PostCSS, protobufjs and Undici. Alphabets 63 to 90 characters; 4 KB to 34 KB. Witness rule,
threshold 2, entries of at most 160 bytes, no whole file.

## Arms

| Arm | What runs | "Fits" when | "Does not fit" when |
| --- | --- | --- | --- |
| Rank | Forced single characters and block rank | the alphabet is within the budget | the bound exceeds the budget |
| Rank + kernel | The above plus `nullspace_kernel_certificate`, and nothing else: no other tier, no exhaustive fallback, no heuristic constructor | as above, or its dictionary replays within the budget | its bound exceeds the budget |
| Baseline | `canzar_lagrangian.py` as frozen here, 60 seconds per query | it returns a dictionary | it returns a certificate |

Each call runs in its own process with a 300-second hard limit.

## Queries

For each corpus, the distinct budgets among: its block rank, one above it, and 64. Duplicates are run once.

## How answers are checked

- Block rank and forced characters are recomputed by `capacity-boundary-v1/evaluate.py`.
- Every kernel dictionary is replayed with the capped checker of `capacity-boundary-v1`.
- A baseline "fits" is replayed by rebuilding a dictionary from the multi-character entries it reports.
- A kernel "+1" rests on the audit in `capacity-kernel-audit-v1`. A baseline certificate is checked by the
  baseline's own exact-fraction verifier. Neither is re-certified independently here.
- Any query where one arm says "fits" and another says "does not fit" is a failure, and work stops.

## Predictions

- **T1.** No arm contradicts another on any query.
- **T2.** At the rank bound, rank + kernel settles at least 9 of the 12 corpora, and rank alone settles only
  those whose rank equals the alphabet.
- **T3.** The kernel builds a dictionary smaller than the alphabet on at least 3 corpora.
- **T4.** At 64 entries, rank alone settles at least 9 of 12, and the kernel changes the answer on at most 2.
- **T5.** Over all distinct queries, the baseline settles no more than rank + kernel does.
- **T6.** On queries both settle, rank + kernel is at least 10 times faster at the median.

## What was known when this was written

On the 23 corpora already seen by this project, rank + kernel alone settles 23 at the rank bound, 20 one
above it and 21 at 64 entries, against 12, 14 and 19 for rank alone (`capacity-kernel-audit-v1`). The
baseline has not been run by me on any real corpus; I ran it once on a three-line made-up corpus to test
the runner.

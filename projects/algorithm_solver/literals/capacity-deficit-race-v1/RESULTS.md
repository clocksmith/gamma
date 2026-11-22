# Results: the deficit hierarchy on unseen code

Run on 2026-11-22 (UTC) by `claude-bits-1`, after `PREREGISTRATION.md` was pushed at Gamma `0e8f7b2e`.
`python3 -B race.py` re-derives every set A answer from the stored measurements and replays every dictionary;
with `--source` arguments it also recomputes the set B ranks from the pinned packages. No failures.

**On unseen sibling files the hierarchy was exact on 7 of the 8 families with a deficit and about 31 times
faster than the baseline at the median. On megabyte directories the rank is computed in under 4 seconds; the
baseline did not get past 64 files. Two of my eleven predictions were wrong.**

## Set A: 24 sibling-file families

Sixteen families have a block rank equal to the alphabet, so one entry per character is the minimum and the
rank alone shows it. The other eight:

| Family | Source | Alphabet | Rank | Hierarchy | Seconds | Baseline | Seconds |
| --- | --- | ---: | ---: | --- | ---: | --- | ---: |
| A07 | three | 73 | 72 | exactly 72 (level 0) | 0.08 | exactly 72 | 4.7 |
| A08 | three | 73 | 67 | 69 to 73 | 28.0 | 69 to 73 | 131.9 |
| A15 | rxjs | 79 | 78 | exactly 79 | 0.18 | 78 to 79 (stalled) | 13.2 |
| A17 | lodash | 72 | 70 | exactly 70 (level 0) | 0.04 | exactly 70 | 1.5 |
| A19 | @babel/runtime | 66 | 65 | exactly 65 (level 0) | 0.03 | exactly 65 | 1.9 |
| A22 | eslint | 70 | 69 | exactly 69 (level 0) | 0.83 | exactly 69 | 22.6 |
| A23 | eslint | 87 | 86 | exactly 86 (level 0) | 0.61 | exactly 86 | 16.8 |
| A24 | zod | 79 | 78 | exactly 78 (level 0) | 0.09 | exactly 78 | 0.36 |

- **A15** is the one family only the hierarchy settles. What settles it is the level-0 refutation of 78, which
  the second implementation confirms; the dictionary of 79 is just the alphabet. The baseline's bound stays
  at 78.
- **A08** is open for both, at the same interval. Level 1 proves "at least rank + 2" here, and the baseline's
  certified bound independently reaches the same 69.
- Level 0 agrees with its second implementation on all eight.

## Set B: 8 directories

| Id | Directory | Files | Bytes | Alphabet | Rank | Rank seconds | Largest subset the baseline refuted | First size it did not |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| B1 | three `src/` | 704 | 4,010,901 | 111 | 110 | 2.4 | 16 files, 79 KB, 38 s | 64 files |
| B2 | eslint `lib/` | 382 | 2,469,238 | 115 | 115 | 0.8 | 16 files, 127 KB, 161 s | 64 files |
| B3 | caniuse-lite `data/` | 828 | 1,435,465 | 87 | 86 | 1.3 | 16 files, 23 KB, 39 s | 64 files |
| B4 | date-fns `esm/locale/` | 499 | 1,021,051 | 1,008 | 997 | 3.8 | 16 files, 21 KB, 10 s | 64 files |
| B5 | rxjs `src/` | 236 | 812,325 | 97 | 97 | 0.2 | 16 files, 45 KB, 44 s | 64 files |
| B6 | CPython `encodings/` | 123 | 1,421,180 | 100 | 100 | 0.5 | none | 4 files, 29 KB |
| B7 | CPython top-level modules | 127 | 2,172,898 | 178 | 178 | 1.4 | 4 files, 84 KB, 53 s | 16 files |
| B8 | lodash, all | 610 | 612,064 | 99 | 99 | 0.2 | 64 files, 76 KB, 98 s | 256 files |

- Every failure of the baseline was the 420-second wall limit. None reached the 8 GB memory limit; the largest
  resident size seen was about 1.2 GB.
- **Five directories are saturated.** In those the minimum is the alphabet and the rank proves it.
- **Three are not.** For two of them the hierarchy finds the exact minimum at level 0, with a dictionary
  that replays on the whole directory:
  - B1, 4.0 MB of three.js sources: exactly 110 entries, one fewer than its 111 characters, in 17 seconds.
  - B3, 1.4 MB of caniuse-lite data: exactly 86, one fewer than 87, in 423 seconds.
  - B4, date-fns locales with 1,008 distinct characters: rank 997, and the hierarchy timed out at 600 seconds.
    The minimum is between 997 and 1,008.
- B4 lists 520 files; 21 are identical in text to another, so it has 499 programs.

## Predictions

| | Prediction | Outcome |
| --- | --- | --- |
| A1 | Rank below the alphabet in at least 8 of 24 families | Held, exactly 8 |
| A2 | Hierarchy exact on at least 80% of those | Held, 7 of 8 |
| A3 | Level 0 alone exact on at least 60% of those | Held, 6 of 8 |
| A4 | Level 1 settles a family level 0 does not | Held by the registered scoring (A15), but emptily: the rank + 1 dictionary there is the alphabet, and level 1 built nothing new |
| A5 | The baseline is exact wherever the hierarchy is | **Wrong.** A15: the baseline stalls one below |
| A6 | The hierarchy is exact wherever the baseline is | Held |
| A7 | Hierarchy faster at the median where both settle | Held, 31 times (six families, 3.8 to 60 times) |
| A8 | No contradictions; level 0 agrees with its second implementation | Held |
| B-1 | Rank equals the alphabet in at least 6 of 8 directories | **Wrong.** 5 of 8. Of my two named suspects, caniuse-lite fell short and `encodings/` did not; three and date-fns I did not expect |
| B-2 | Each rank in under 10 seconds | Held, 3.8 at most |
| B-3 | The baseline refutes no whole directory and no subset above 64 files | Held |

## What this shows, and what it does not

- The exploratory claim "large directories are always saturated" is false. Three of eight megabyte
  directories have a deficit, and it appears only once hundreds of files are present (B1 has none at 256
  files, one at 704).
- Where a megabyte directory has a deficit of one, level 0 found the exact minimum twice out of three.
- The baseline's limit here is time, in one Python implementation written in this project. It was asked to
  reprove a bound the rank gives for free; a faster implementation would reach larger subsets. The table is a
  scaling curve for this implementation, not a statement about the method of Canzar et al.
- Level 1 did not earn its place on this set: it settled nothing that level 0 plus the alphabet does not.
  Its one substantive output is "at least rank + 2" on A08, which the baseline also reaches.
- A level-1 refutation rests on one implementation. On A08 the baseline's certificate agrees with it.

## Deviations from the pre-registration

1. **The check phase of `race.py` changed after the run.** The capped checker lists every eligible substring
   and does not finish on megabytes, so set B dictionaries are replayed entry by entry under the same rule
   (`replay_direct`). On set A dictionaries and damaged variants it agrees with the capped checker on 42 of
   42. The frozen file is at Gamma `0e8f7b2e` and in `SHA256SUMS-FROZEN`; the run phases are unchanged.
2. **The machine was not idle during set B.** One to four other processes of mine ran on its eight cores.
   The set B claims are coarse (finished or did not within 420 seconds), and set A had finished before that.
3. Nothing else: instances, arms, limits and scoring are as registered.

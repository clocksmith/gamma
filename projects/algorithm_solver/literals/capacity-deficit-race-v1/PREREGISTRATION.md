# Pre-registration: the deficit hierarchy on unseen code

Committed on 2026-11-22 (UTC) by `claude-bits-1`, before any rank, bound, dictionary or baseline call was
computed on either set. The selection script reads files, sizes and names only. `race.py` was tried on three
corpora this project had already seen (P01, P03 and P06 of `capacity-lagrangian-race-v1`) and on nothing else.

## Questions

1. **Set A.** On small families of sibling files, how often is the block rank below the alphabet, and when
   it is, does the deficit hierarchy (`capacity-deficit-v1`, levels 0 and 1) find the exact minimum
   dictionary? How does it compare with the shortest-path Lagrangian baseline?
2. **Set B.** On whole directories of hundreds of files, is one entry per character still optimal, how long
   does the rank computation take, and can the baseline certify the same bound at that size?

## Sources

Ten public packages at exact versions, listed with licences in both instance files: the CPython 3.14.2
standard library and the npm packages three 0.186.0, rxjs 7.8.2, lodash 4.18.1, @babel/runtime 7.28.4,
ajv 8.18.0, eslint 9.39.2, zod 3.25.76, caniuse-lite 1.0.30001810 and date-fns 2.30.0. None of these files
was used by this project before, except that four CPython packages (asyncio, multiprocessing, sqlite3,
unittest) were, and are excluded from set A.

All 277 CPython files were compared with the tag `v3.14.2` upstream and match. Two files that the installer
or the build adds (`sitecustomize.py`, `_sysconfigdata__darwin_darwin.py`) are not in the tag and were
excluded by name; that changed the selection once, before anything was computed. The npm files are as
installed and were not compared with the registry.

## Set A: 24 sibling-file families (`instances-a.json`, texts included)

`select_instances.py`, seed `capacity-deficit-race-v1/2026-11-22`. Per source, the directories holding at
least six files of the source's extension between 300 and 4,000 bytes are shuffled; a family is 3, 4 or 6
files that are consecutive in name order inside one directory. Families never share a file. Six families
come from CPython, five from three, four from rxjs, two each from lodash, @babel/runtime, ajv and eslint,
and one from zod. Sizes: 2.5 KB to 17.7 KB; alphabets 58 to 87 characters.

SHA-256 `89b020c6ee4a39fb547021db20af13a3a12be06f17a094455a7e67eb6a9a0ecc`.

## Set B: 8 directories (`instances-b.json`, paths and SHA-256 only)

Every file of the extension between 200 and 60,000 bytes under the subtree, files as programs. The eight
subtrees were named by hand from file counts and byte totals alone.

| Id | Subtree | Files | Bytes |
| --- | --- | ---: | ---: |
| B1 | three `src/` | 704 | 4,010,901 |
| B2 | eslint `lib/` | 382 | 2,469,238 |
| B3 | caniuse-lite `data/` (generated data, not hand-written code) | 828 | 1,435,465 |
| B4 | date-fns `esm/locale/` | 520 | 1,050,439 |
| B5 | rxjs `src/` | 236 | 812,325 |
| B6 | CPython `encodings/` | 123 | 1,421,180 |
| B7 | CPython top-level modules | 127 | 2,172,898 |
| B8 | lodash, all | 610 | 612,064 |

SHA-256 `7e9941e3d085d29c8830cf27412f0efdd655253fe3f629527d2d1b9ce474a9a4`. Sets A and B overlap in files;
they answer different questions.

## Rule

Witness rule, threshold 2: single characters, and longer substrings of at most 160 UTF-8 bytes that occur in
at least two files; no whole file.

## Arms on set A

Each call is its own process with a 600-second wall limit. Three families run at a time, so times are
comparable between arms but are not clean single-process timings.

| Arm | What runs | Counts as exact when |
| --- | --- | --- |
| Rank | Forced cuts and block rank | the rank equals the alphabet |
| Hierarchy | `capacity-deficit-v1/deficit.py`, `analyze(programs, 'W2')`, default limits, as committed at Gamma `47061f70` | its lower bound equals the size of a dictionary it built, replayed by the capped checker of `capacity-boundary-v1` |
| Baseline | `capacity-lagrangian-race-v1/canzar_lagrangian.py` as frozen there. It is given the block rank and asked budgets in ascending order from it, jumping to its own certified bound, until it returns a dictionary or stops refuting; 600 seconds in total | its refutations reach the budget at which it returns a dictionary that is rebuilt and replayed |

The hierarchy and the baseline run only where the rank is below the alphabet. If the hierarchy times out it
is rerun at level 0 only and scored on that. The second implementation of the level-0 test
(`capacity-kernel-audit-v1/independent_kernel.py`) runs alongside as a cross-check, not as an arm.

## Arms on set B

- **Rank.** Forced cuts and block rank in two prime fields, on the whole directory and on seeded random
  subsets of 4, 16, 64 and 256 files.
- **Baseline.** On each subset in ascending size and then the whole directory, it is asked to refute one
  entry fewer than the block rank, which is always a true refutation. 300 seconds inside the method, 420
  seconds wall, 8 GB of memory; the run for a directory stops at the first size it does not refute. Two
  directories run at a time.
- **Hierarchy.** Only on a directory whose rank is below its alphabet; 600 seconds.

The baseline is one Python implementation written in this project, not the authors' code. A faster
implementation would move the sizes it reaches, so set B reports a measured scaling curve for this
implementation and nothing more general.

## How answers are checked

- Block ranks on set A are recomputed by `capacity-boundary-v1/evaluate.py`. Set B ranks can be recomputed
  from the pinned packages with `race.py --source ...`.
- Every dictionary is replayed with the capped checker.
- A level-0 refutation is compared with the second implementation. A level-1 refutation rests on one
  implementation and on the exhaustive audit in `capacity-deficit-v1`; it is flagged as such.
- A baseline refutation is checked by the baseline's own exact-fraction verifier, not independently.
- If one arm's lower bound exceeds another arm's replayed dictionary, that is a failure and work stops.

## Predictions

Set A:

- **A1.** The block rank is below the alphabet in at least 8 of the 24 families.
- **A2.** Among those, the hierarchy is exact on at least 80%.
- **A3.** Among those, level 0 alone is exact on at least 60%.
- **A4.** Level 1 settles at least one family that level 0 does not.
- **A5.** The baseline is exact on every family where the hierarchy is exact: no gain in what can be settled
  at this size.
- **A6.** The hierarchy is exact on every family where the baseline is exact.
- **A7.** On families both settle, the hierarchy is faster at the median.
- **A8.** No arm contradicts another, and level 0 agrees with its second implementation everywhere.

Set B:

- **B-1.** The block rank equals the alphabet in at least 6 of the 8 directories. The two I think most likely
  to fall short are CPython `encodings/` and caniuse-lite `data/`, which are generated from templates.
- **B-2.** The rank of each whole directory is computed in under 10 seconds.
- **B-3.** The baseline refutes within its limits on no whole directory, and on no subset of more than 64
  files.

## What was known when this was written

- On the 35 corpora already seen, the hierarchy is exact on 33, level 0 alone on 31; 13 of the 35 have a
  rank below the alphabet. The baseline settled all 34 queries of the three-arm race, and on the two open
  corpora (PY-3, B04) it does not close the gap either.
- On five large directories from this project's own repositories (exploratory), the rank equalled the
  alphabet every time, and already for two files in a shuffled order.
- Nothing here costs money. No model is called.

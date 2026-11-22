# Pre-registration: cheap checks against the flow method on unseen projects near 64 characters

Committed on 2026-11-22 (UTC), before any method was run on the nine corpora below. Only their sizes were
measured: files, bytes, alphabet and the number of eligible occurrences.

## Question

A grid of 64 keys has room for 64 dictionary entries. For a project that uses more than 64 distinct
characters, one key per character does not fit. Shared fragments can still make it fit. Which method tells
you, how fast, and does the answer change which grid you would build?

This says nothing about how many presses a grid takes to use. That is a separate comparison.

## Corpora

Chosen by the seeded rule in `select_corpora.py` from four public repositories at pinned commits. A corpus
is four files of one language from one directory. Rule: witness rule, threshold 2; the four files are the
programs. Directories used by the earlier independent evaluation are excluded.

| Corpus | Repository | Directory | Bytes | Alphabet | Eligible occurrences |
| --- | --- | --- | ---: | ---: | ---: |
| JS-1 | doppler | `src/inference/tokenizers` | 3,844 | 69 | 30,833 |
| JS-2 | doppler | `src/config/schema/platform` | 3,446 | 66 | 117,084 |
| JS-3 | fawn | `bench/external-projects/wgsl-fns` | 2,517 | 70 | 94,337 |
| PY-1 | fawn | `runtime/c/compiler/independent_tests_m5` | 4,840 | 69 | 59,542 |
| PY-2 | gamma | `tools` | 3,894 | 69 | 58,785 |
| PY-3 | fawn | `runtime/c/compiler/independent_tests_m10/postdisclosure` | 5,892 | 68 | 2,522,013 |
| C-1 | gamma | `projects/enwiki9/results/fx2_expert_confirm1m_v1/work/P/src/mixer` | 3,307 | 69 | 25,241 |
| C-2 | gamma | `projects/enwiki9/results/fx2_weight_native_fixture50051_q0_v1/work/source/external/fx2-cmix-transformer-v1/src/coder` | 2,500 | 67 | 65,129 |
| C-3 | fawn | `runtime/c/compiler/targets/metal/tests/host` | 3,848 | 70 | 41,389 |

- The rule asked for four corpora per language. Nine exist under its limits.
- Every alphabet is above 64, so one key per character fits none of them.
- The first run of the rule chose two corpora that duplicated others. A no-shared-file condition was added,
  before any method was run. It is stated in the script.
- The rule's author also wrote the methods. The rule is mechanical and can be rerun from the pins.

## Methods, under identical entry rules

| Method | What it returns |
| --- | --- |
| Cheap checks | Forced single characters and the rank of the forced blocks: a lower bound. Recomputed by `evaluate.py`. |
| Shipped diagnostic | `capacity-diagnostic-v1/diagnostic.py` at budget 64: `IMPOSSIBLE`, `FEASIBLE` or `UNRESOLVED`. |
| Flow method | The flow formulation of Canzar et al. (2012) on a general solver: a linear program for a lower bound, an integer program for a dictionary. |

The flow method here is a reimplementation of the published formulation on HiGHS. It is not the authors'
software and does not use their Lagrangian search.

Limits, fixed here: 600 seconds per linear program and per integer program; 900 seconds for the diagnostic.
Above 500,000 eligible occurrences the linear program is not attempted and the dictionary search uses only
entries of at most 40 characters. PY-3 is over that limit.

## What counts as an answer

- **Lower bound:** forced single characters, block rank, or a stored certificate checked in exact fractions.
- **Upper bound:** the alphabet, or a stored dictionary replayed against the frozen bytes.
- **Fits 64:** a replayed dictionary of at most 64 entries. **Does not fit:** a lower bound above 64.
- **The grid decision changes** when the alphabet is above 64 and the project fits.
- A solver's claim of optimality is recorded and not used.

## Predictions

- **B1.** Block rank equals the minimum on every corpus whose minimum is established.
- **B2.** The flow method establishes the minimum on at least 7 of the 8 corpora under the size limit.
- **B3.** Between 2 and 4 of the 9 corpora fit 64 entries, and JS-2 is one of them.
- **B4.** Every corpus shown not to fit is certified by block rank alone. No corpus shown to fit is
  certified by the cheap checks or by the shipped diagnostic; each needs a dictionary from the search.
- **B5.** The cheap checks take under 1 second on every corpus. The flow method takes at least 50 times as
  long on every corpus it finishes.
- **B6.** The alphabet exceeds the minimum by 1 to 8 on every corpus whose minimum is established.

## Proved claims. A violation means a checker is wrong, and work stops.

- A stored certificate is valid and no lower bound exceeds the size of a replayed dictionary.
- A stored dictionary has only eligible entries and spells every file byte for byte.

## What was known when this was written

- On the two C corpora settled in `capacity-complexity-v1`, block rank was exact (61 and 65) and the alphabet
  exceeded the minimum by 3 and 2.
- The runner was tried on those two corpora only: 12 and 45 seconds for the flow method, 0.03 and 0.06
  seconds for the cheap checks.
- Nothing was run on the nine corpora above.

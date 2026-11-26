# `objective-holdout-v1`

One small frozen comparison: five ways of choosing a code vocabulary are trained on the same 400 CodeNet files,
frozen, and scored on files none of them has seen. It asks which rule uses fewer tokens and which makes
smaller complete archives out of sample. It does not search for a best dictionary.

Read [`PREREGISTRATION.md`](PREREGISTRATION.md) first. [`FORMAT.md`](FORMAT.md) defines the archive.

To check and reproduce it, copy and paste one command. It needs no network:

```
python3 replay.py all --strict
```

It takes 109 s from a clean clone and exits 0 only if every step passes. It needs Python 3, a C compiler and zstd
1.5.7; with another zstd version `--strict` fails on the steps that could not be compared in full, so drop the flag
and read the lines marked `PART`. The levels inside it can be run alone:

```
python3 replay.py check    # 5 s: integrity, split boundaries, receipts, seven files end to end
python3 replay.py score    # 36 s: rescore all four sets, compare with the committed results
python3 replay.py train    # 59 s: retrain every dictionary, compare byte for byte
python3 replay.py posthoc  # 9 s: recompute the measurements made after scoring, compare
```

This command is the verification. The frozen scripts it wraps are not, run alone: see "Known limits of the frozen
code" below. The same holds for the older standalone checker of the earlier transfer experiment,
[`../witness-length-sweep-v1/check_unseen_transfer.py`](../witness-length-sweep-v1/check_unseen_transfer.py): it
is partial, and [`../witness-length-sweep-v1/VERIFY.md`](../witness-length-sweep-v1/VERIFY.md) gives the command
that completes it.

`check` alone needs only Python 3 and zstd. Replaying the selection of the test files is separate: it needs the 568 MB CodeNet mirror and IBM's
Python near-duplicate file (see `select_fresh_codenet.py`); `check` verifies the committed selection against IBM's
identical-problem list and the rank order instead.

| File | Role |
| --- | --- |
| `replay.py` | The entry point for checking and reproducing everything below |
| `train_arms.py` | Trains every arm on `train` only and writes `frozen/` |
| `score.py` | Frozen scoring command: tokens, real archive bytes, reuse, rent, paired counts, zstd |
| `select_fresh_codenet.py`, `select_project.py` | Sample rules for the two test sets, run by the scorer |
| `bits_oh.py`, `test_bits_oh.py` | Format library and its checks |
| `audit_zero_escape_misses.py` | Separate: classifies the failures of the earlier zero-escape transfer test |
| `explore_posthoc.py` | Post hoc and exploratory, after the reviews: the token-gain and BPE orders cut at equal sizes, unseen problems split by language and by author, how often chosen fragments occur in training, zstd with lean framing, overlap with the closest training file as Jaccard similarity and as a share of the file's own substrings, and which fragments are used under each parse |
| `audit_near_duplicates.py`, `out/near-duplicate-audit.json` | A receipt written after scoring: the frozen selection dropped no problem as a Python near-duplicate, which only means something if it could have. 219 of the 400 earlier Python submissions are in one of IBM's 367,768 clusters, with 2,379 near-duplicates between them; none of the 200 unseen submissions is among those. Needs IBM's 40 MB cluster file; `check` reads the receipt |
| `explore_support.py` | Post hoc and exploratory, written after scoring: how a fragment's support in training relates to whether it pays for its storage on the test sets |
| `make_results.py`, `RESULTS.md`, `out/rule-outcomes.json` | The results, generated from `out/results-*.json`. The six preregistered rules are evaluated in one function; `RESULTS.md` and the paper read the outcomes file. A sentence that states an outcome is built from the data or stops the script when the data no longer supports it |
| `test_replay.py` | Breaks receipts on purpose and requires every check to refuse; run by `replay.py check` |
| `SCORER-LOG.md`, `independent_decode.py`, `DEVIATIONS.md` | What the scorer ran, its own decoder, and the one recorded deviation |
| `metadata/` | IBM's identical-problem clusters (CDLA-Permissive-2.0) |

## Known limits of the frozen code

Files listed in `SHA256SUMS-FROZEN` are never edited, and [`../fixed-source-v3/engine.c`](../fixed-source-v3/engine.c)
is pinned by hash in four freeze records. A review on 2026-11-26 found gaps in them; each is closed in `replay.py`,
which is not frozen, and none changed a frozen result.

| Gap in a frozen file | What could go wrong | Where it is closed | The frozen run |
| --- | --- | --- | --- |
| `train_arms.py` does not read the engine's `stopped=1` | On a slow machine a time-limited chain is shorter than the cap and the dictionary is silently small | `replay.py train` reads every chain's last line and entry count | All four arms returned 3,925 fragments, the slowest in 28.8 s of 300 s (`check` reads this from the receipts) |
| `train_arms.py` reuses an `engine` binary found in `--work` but records the hash of the current source | After a source edit, the recorded hash names code that did not run | `replay.py train` starts from an empty work directory, and `check` compares `engine.c` with the recorded hash | The four chains equal chains an earlier, separately built binary produced |
| `engine.c` BPE: the pair table has 2^20 slots and does not grow; a full table never returns, and the time limit is only read between rounds | A hang on a corpus with more than about a million token positions | `replay.py train` runs the trainer in its own session and kills it after 1,800 s | 259,706 bytes, far below the table size |
| `engine.c` writes its chain in place; only the last line (`D ... stopped=0`) marks a finished run | A killed run leaves a file that looks like a chain | `replay.py train` requires that line and the full entry count; [`../codenet-replication-v1/run_replication.py`](../codenet-replication-v1/run_replication.py) now writes to a temporary name and resumes only from finished chains | Chains are rebuilt in a fresh directory on every replay |
| `FORMAT.md` tells a decoder to ignore padding, so `independent_decode.py` measures padding and accepts any | Junk after the last file would decode as valid | `replay.py check` and `score` require under one byte of padding, all zero, and read every verdict in the decoder's report | 80 archives: at most 7 padding bits, all zero |

A new experiment that needs a different engine should copy `engine.c` under a new name, not edit it.

These gaps are closed only when `replay.py` is what is run. `independent_decode.py` run alone still reports
`all_ok` with junk after the last file, and `train_arms.py` run alone still accepts a time-limited chain and a stale
engine binary. Neither is a verification without `replay.py`.

CodeNet files are IBM Project CodeNet v1.0.0 under CDLA-Permissive-2.0; see
[`../codenet-replication-v1/NOTICE`](../codenet-replication-v1/NOTICE).

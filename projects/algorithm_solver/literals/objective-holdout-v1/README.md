# `objective-holdout-v1`

One small frozen comparison: five ways of choosing a code vocabulary are trained on the same 400 CodeNet files,
frozen, and scored on files none of them has seen. It asks which rule uses fewer tokens and which makes
smaller complete archives out of sample. It does not search for a best dictionary.

Read [`PREREGISTRATION.md`](PREREGISTRATION.md) first. [`FORMAT.md`](FORMAT.md) defines the archive.

To check or reproduce it, one command, no network:

```
python3 replay.py check    # 5 s: integrity, split boundaries, six files end to end
python3 replay.py score    # 42 s: rescore all four sets, compare with the committed results
python3 replay.py train    # 62 s: retrain every dictionary, compare byte for byte
```

`check` needs Python 3 and zstd; `train` also needs a C compiler. zstd rows are compared only when the local zstd
is 1.5.7. Replaying the selection of the test files is separate: it needs the 568 MB CodeNet mirror and IBM's
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
| `explore_support.py` | Post hoc and exploratory, written after scoring: how a fragment's support in training relates to whether it pays for its storage on the test sets |
| `make_results.py`, `RESULTS.md` | The results, generated from `out/results-*.json` |
| `SCORER-LOG.md`, `independent_decode.py`, `DEVIATIONS.md` | What the scorer ran, its own decoder, and the one recorded deviation |
| `metadata/` | IBM's identical-problem clusters (CDLA-Permissive-2.0) |

CodeNet files are IBM Project CodeNet v1.0.0 under CDLA-Permissive-2.0; see
[`../codenet-replication-v1/NOTICE`](../codenet-replication-v1/NOTICE).

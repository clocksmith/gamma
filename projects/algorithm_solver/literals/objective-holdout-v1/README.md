# `objective-holdout-v1`

One small frozen comparison: five ways of choosing a code vocabulary are trained on the same 400 CodeNet files,
frozen, and scored on files none of them has seen. It asks which rule uses fewer tokens and which makes
smaller complete archives out of sample. It does not search for a best dictionary.

Read [`PREREGISTRATION.md`](PREREGISTRATION.md) first. [`FORMAT.md`](FORMAT.md) defines the archive.

| File | Role |
| --- | --- |
| `train_arms.py` | Trains every arm on `train` only and writes `frozen/` |
| `score.py` | Frozen scoring command: tokens, real archive bytes, reuse, rent, paired counts, zstd |
| `select_fresh_codenet.py`, `select_project.py` | Sample rules for the two test sets, run by the scorer |
| `bits_oh.py`, `test_bits_oh.py` | Format library and its checks |
| `audit_zero_escape_misses.py` | Separate: classifies the failures of the earlier zero-escape transfer test |
| `metadata/` | IBM's identical-problem clusters (CDLA-Permissive-2.0) |

CodeNet files are IBM Project CodeNet v1.0.0 under CDLA-Permissive-2.0; see
[`../codenet-replication-v1/NOTICE`](../codenet-replication-v1/NOTICE).

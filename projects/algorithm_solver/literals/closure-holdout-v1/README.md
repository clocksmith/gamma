# closure-holdout-v1

Separates the two differences between byte pair encoding and greedy token-gain vocabulary selection: the
objective (pair count against exact token gain) and the structure (every entry a concatenation of two earlier
entries, or any substring). One new arm, `closed`, keeps token gain's objective and BPE's structure.
See [PREREGISTRATION.md](PREREGISTRATION.md) for the question, rules and order of work.

| File | Purpose |
| --- | --- |
| `engine_closed.c` | Frozen fixed-source-v3 engine, included unchanged, plus mode `greedy-closed` |
| `train.py` | Builds `bpe`, `token`, `closed` on CodeNet `primary`; checks `bpe` and `token` equal the frozen objective-holdout-v1 dictionaries; writes `frozen/` |
| `dev_eval.py` | Development check on `train` and `dev` only |
| `select_fresh2.py`, `select_projects.py` | Test-set rules, run by the scorer after the freeze |
| `score.py` | Tokens, single-byte share, equal-size grid, paired sign tests, decision rules |

Rebuild the dictionaries (about 40 s, C compiler and Python 3):

```sh
python3 -I train.py --work /tmp/closure-work
```

# How to check this folder (added 2026-11-26)

`README.md`, `RESULTS.md`, the runner and `check_unseen_transfer.py` are frozen by the three checksum lists here
and are not edited. This note is not frozen. It exists because the frozen README tells you to run
`check_unseen_transfer.py`, and that checker is **partial**: it does less than it says.

Run this instead. It runs the frozen checker and then the checks the frozen one skips:

```sh
python3 -B recheck_unseen_transfer.py     # 43 s, Python 3 only, writes nothing
```

What the frozen checker does not do, although its docstring and `RESULTS.md` say or imply it:

| Not checked by `check_unseen_transfer.py` | Consequence |
| --- | --- |
| The recorded unseen-gain attributions (item 3 of its docstring) are never replayed | "The only +2 gain uses single characters only" was unverified |
| `charOptTrain` and `charOptTest` are compared only with the CSV written by the same run | The training lift of +1 to +4 in `RESULTS.md` rested on a number nothing checked |
| 19 of the 24 CSV columns | A CSV that disagreed with the JSON outside five columns would pass |
| Rows that name no dictionary; the count of multi-character entries | Unverified |

On a copy of the results with a wrong training baseline and a false attribution, `check_unseen_transfer.py` prints
`ALL TRANSFER VERIFIED` and `recheck_unseen_transfer.py` fails on both. On the files as committed, every figure
`RESULTS.md` quotes reproduces: 118 budgets where the joint dictionary beat single characters in training, a training
lift of +1 to +4, an unseen lift of -3 to 0, and no unseen gain that needs a multi-character fragment.

So the results stand, and "verified by `check_unseen_transfer.py`" in `RESULTS.md` should be read as "verified by
`recheck_unseen_transfer.py`". The record of the review is [`../REVIEW-20261126.md`](../REVIEW-20261126.md).

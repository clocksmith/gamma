# Addendum: the benchmark under the 160-byte entry cap

Written on 2026-11-22 (UTC), after the pre-registered run and before `capped.py --run` was run.

## Why

The pre-registration said the three methods run under identical entry rules. They did not. The shipped
diagnostic, like `sixbit-v1`, allows a multi-character entry of at most 160 UTF-8 bytes. The flow method and
the certificate and replay checks used here had no cap. I did not check this before freezing. The mistake
is mine.

It showed on JS-2: the shipped diagnostic certifies a lower bound of 65, and the uncapped flow method found
a replayed dictionary of 64 entries. Two of its entries are 246 and 175 characters long. Both answers can
be right, each under its own rule.

## What this run does

It reruns the flow method on the same nine frozen corpora with the cap applied to the eligible entries, the
certificate check and the dictionary replay. The cheap checks do not depend on the cap. Limits are
unchanged.

## What is known beforehand, so nothing here is a prediction

- All uncapped results: eight minimums, and 51 to 66 for PY-3.
- A lower bound proved without the cap holds with it. A dictionary found without the cap is legal with it
  only if every entry is within 160 bytes.
- The uncapped dictionaries for JS-2 and C-2 have an entry over the cap (246 and 161 characters).
- The shipped diagnostic's capped lower bounds: 65 on JS-2, 57 on PY-3.

The pre-registered run and its results stay as they are, under the uncapped rule they were run with.

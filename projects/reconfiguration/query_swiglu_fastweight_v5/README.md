# B1 v5: compile a table of examples into a small adapter

Development status. Nothing here is confirmed: the protocol in `protocol_v5_draft.json` is a
draft for review, no confirmation task has been generated, and every number below comes from
the `dev` task split.

## What it does

Give the model a table of worked examples ("this item gets this code"). v5 runs the table
through the frozen model once, and solves a ridge regression in closed form that turns the
table into one low-rank update on one MLP layer. With that update switched on, the model answers
new questions with the table removed. Switching it off restores the base model exactly.

The use is cost: the table is paid for once at compile time and not again on every question.

What the task is: every question is about a noun that is not in the table. The model has to place the new
noun in one of the table's four groups and return that group's code. That is classification by example. It is
not recall of a stored item, which nothing here tests.

## Prior work

Compiling labelled examples into weights in closed form, with no gradient step, is not new. FAAST (Bao et al.,
arXiv 2605.04651, May 2026) does it with least squares and a trained readout, and reports its closed-form
map, a linear probe and kNN within about 2 points of each other on few-shot classification. This study does
not claim the mechanism. It tests a systems result: with the table removed, how close is accuracy to the
model given the table, and at how much less state and time, on Q4K models in Doppler's WebGPU runtime.

## What changed from v4

v4 is sealed and negative. Reading its compiler found these defects; v5 fixes each.

| v4 | v5 |
|---|---|
| Guessed where the answer starts and picked the `-` or `/` inside multi-part answers | The caller passes the token the question ends with |
| Fitted several layers independently on activations captured with no adapter on | One layer per table |
| Layer fixed in advance | Layer chosen per table by leave-one-out accuracy on the table itself |
| Ridge fixed at 0.15 of total energy, which shrinks the directions that separate groups | Ridge chosen by the same leave-one-out check |
| Features weighted by their correlation with 12 labels | Features scaled by their own spread |
| Background rows weighted twice | Weighted once |
| No self-check | Reports leave-one-out accuracy; stays off when it is at chance |

v4's test was also at the floor: with the table in its prompt the base model scored 22 of 64 on
single-token answers where a constant guess scores 16. v5's tasks are ones the base model can do.

## What development showed

The first three rows of that table are what matter. The last four (choosing the layer and ridge
per table, and the self-check) were tried and made things worse; the adapter that works is the
fixed one on the top two layers. Details and numbers are in [RESULTS.md](RESULTS.md).

## Files

- `fastweight_v5.mjs`: the compiler.
- `run_v5.mjs`: the runner. Its `top2_*` arms are the fixed adapter (the result); its `v5_*` arms are the
  per-table selected adapter (worse).
- `controls_v5.mjs`: three controls that answer without the adapter: the most frequent support code, a plain
  classifier, and a nearest-neighbour vote, the last two on the same activations and support lines the adapter
  is fitted on (`mfc_bare`, `probe_bare`, `nn_bare`; `B1_WITH_CONTROLS=1`). Unit-tested on CPU.
- `tasks_v5.py`: task generator with disjoint `dev` and `confirm` item groups. Confirmation uses 37 groups in
  a block design: 111 tables, any two sharing at most one group.
- `tally_v5.py`, `table_level_v5.py`: counts and paired tests from a receipt, per question and per table.
- `audit_v5.py`, `power_v5.py`, `design_power_v5.py`: error shape, power, and whether the table-level test
  is calibrated when tables share groups.
- `gate_v5.py`: the gate itself from receipts: exact one-sided sign-flip test with the 5-point margin, bootstrap
  interval, group-aware test, controls and cached-prompt parity.
- `replay_compare_v5.py`: whether a replay reproduces an earlier receipt, arm by arm.
- `design_check_v5.py`, `controls_v5.test.mjs`: checks that need no model.
- `protocol_v5_draft.json`: the draft protocol, for review before any lock.

## Run

One WebGPU process at a time, after confirming the GPU is free.

```
B1_RESOURCE_CHECK="<who confirmed the GPU is free>" \
  node run_v5.mjs DOPPLER_ROOT MODEL_DIR OUT.json dev SEED TABLES SHOTS_PER_GROUP QUERIES_PER_GROUP
python -I tally_v5.py OUT.json
```

Optional arms: `B1_WITH_SHUFFLED=1` (wrong-label adapter), `B1_WITH_KV_SNAPSHOT=1` (cached prompt),
`B1_WITH_CONTROLS=1` (most-frequent code and plain classifier).

Checks with no model or GPU:

```
python3 -I design_check_v5.py            # nouns, development tasks unchanged, confirmation design, 25% control
node --test controls_v5.test.mjs         # the two controls
python design_power_v5.py RECEIPT_DIR OUT.json   # needs numpy
python3 -I gate_v5.py RECEIPT.json [...]  # the gate, per model
```

Results are in [RESULTS.md](RESULTS.md).

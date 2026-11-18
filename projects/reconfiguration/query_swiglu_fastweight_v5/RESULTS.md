# B1 v5 development results

Exploratory. `dev` split only, no locked protocol. Receipts are in
`.work/query-swiglu-fastweight-v5/`; `tally_v5.py` reproduces every count.

## Two adapters were tried; the simple one is the result

- **Fixed** (`top2_*` arms in the receipts): the top two layers, ridge fixed at 0.15. This is
  v4's layout with its defects fixed: the anchor comes from the question format, features are
  scaled by their own spread, background rows are weighted once.
- **Selected** (`v5_*` arms): one layer and one ridge strength chosen per table by leave-one-out
  accuracy. This was the main new idea, and it is worse. See "What did not work".

## Fixed adapter, table removed, against the base model with the table present

64 questions per run. Seeds 1003 and 1004 were run once, after the fixed adapter's code was
final; it was never tuned on them.

| Model | Examples per group | Seed | Base, table present | Fixed adapter, table removed | Wins / losses | Seconds per question, base / adapter |
|---|---:|---:|---:|---:|---:|---:|
| Qwen3.5-0.8B | 3 | 1001 | 35 | 38 | 13 / 10 | 1.01 / 0.37 |
| Qwen3.5-0.8B | 3 | 1003 | 32 | 33 | 10 / 9 | 1.00 / 0.24 |
| Qwen3.5-0.8B | 20 | 1002 | 58 | 59 | 4 / 3 | 5.92 / 0.50 |
| Qwen3.5-0.8B | 20 | 1004 | 52 | 57 | 9 / 4 | 5.67 / 0.21 |
| Qwen3.5-2B | 3 | 1001 | 41 | 46 | 11 / 6 | 2.17 / 0.67 |
| Qwen3.5-2B | 3 | 1003 | 35 | 41 | 12 / 6 | 2.68 / 0.57 |
| Qwen3.5-2B | 20 | 1002 | 59 | 57 | 3 / 5 | 13.47 / 0.54 |
| All seven runs | | | 312 / 448 | 331 / 448 | | |

- The base model with the table removed scores 0 of 448. Guessing one of the four valid codes
  would score 112.
- With the table removed, the fixed adapter is level with or ahead of the base model that has
  the table, in six runs of seven. No single run is significant (smallest exact McNemar p is 0.24).
  The claim the data supports is "not worse", at 3 to 25 times less time per question.
- With the table also present, the fixed adapter scores 343 of 448 against the base model's 312.
  One run reaches p = 0.035 (Qwen3.5-0.8B, seed 1001, 12 wins and 3 losses).
- The fixed adapter emits a valid code in 445 of 448 table-removed answers.
- Adapters are 110 to 200 KB. Compile times in the receipts (4 to 63 s per table) include
  capturing sixteen layers for the selected adapter; the fixed adapter needs two.

## What did not work

- **Per-table selection of layer and ridge.** With the table removed, the selected adapter
  scores 280 of 448, below the fixed adapter (331) and the base model with the table (312).
  When the leave-one-out check picks a layer below the last one, the first token is usually
  right but the stop signal fails and the answer runs on ("omega. omega"). The write-strength
  check only looked at the first token. Breaking ties toward a stronger ridge (commit
  `8d3272084`) made it worse on fresh seeds, not better.
- **Reading middle layers.** At the token where the answer begins, leave-one-out accuracy is at
  chance through the middle of the model and rises only in the last three or four layers.
- **Small models with three examples.** With three examples per group the base model itself is
  only at 50 to 64 percent, so there is little to retain.

## Limits

- Development tasks written by the same session that wrote the compiler; two models from one
  family; 64 questions per run.
- A cached copy of the prompt would give the base model's with-table accuracy at about the
  table-removed time. That comparison is not run. The adapter's case against it is size and
  freed context.
- Seeds 1001 and 1002 were looked at while the selected adapter was being changed. The fixed
  adapter's code did not change between any of the runs.

## Runs with same-prompt baselines (2026-11-18, fresh seeds, fixed adapter compiled alone)

64 questions per run. Arms with the table present unless marked.

| Model | Examples per group | Seed | Base | Fixed adapter | Nearest-neighbour cache | Context-aware decoding | Fixed adapter, table removed |
|---|---:|---:|---:|---:|---:|---:|---:|
| Qwen3.5-0.8B | 3 | 1005 | 37 | 41 | 43 | 38 | 34 |
| Qwen3.5-2B | 3 | 1005 | 46 | 47 | 46 | 44 | 40 |
| Qwen3.5-0.8B | 20 | 1006 | 59 | 62 | 59 | 57 | 55 |
| Total | | | 142 | 150 | 148 | 139 | 129 |

- With the table present the fixed adapter is ahead of the base model in all three runs, by 1 to 4
  questions; no run is significant, and a nearest-neighbour cache over the table's own answers is
  about level with it (148 against 150). On this evidence the adapter has no clear examples-present
  advantage over that cache.
- With the table removed the fixed adapter trails the base model with the table in all three of
  these runs (129 against 142), which is weaker than the earlier seven runs (331 against 312).
- Compiling the fixed adapter alone took 2.1 to 2.6 s per 12-line table on Qwen3.5-0.8B.

## Table-level reanalysis by the new B1 owner (2026-11-18, no new run)

`power_v5.py` over all ten development receipts. The unit is the support table and the number is the
difference in accuracy between two arms on that table.

| Comparison | Tables | Mean difference | Better / worse / equal | Sign-flip p |
|---|---:|---:|---:|---:|
| Fixed adapter against base, table present | 64 | +6.3 points | 35 / 9 / 20 | 0.007 |
| Fixed adapter against nearest-neighbour cache, table present | 20 | +0.3 points | 5 / 4 / 11 | 1.0 |
| Nearest-neighbour cache against base, table present | 20 | +3.8 points | 10 / 2 / 8 | 0.29 |
| Fixed adapter, table removed, against base with the table | 64 | +1.2 points | 26 / 22 / 16 | 0.68 |

- With the table present the adapter is ahead of the base model at the table level. That is development
  data: some seeds were seen while code changed, and the three runs made afterwards show +4.1 points over
  20 tables (p 0.45).
- It is not ahead of the nearest-neighbour cache. Both are a vote from the table's own examples added at
  the output, so there is no mechanism by which the adapter should beat the cache with the table present,
  and the data shows none. An examples-present claim of "better than a cache" is not supported.
- With the table removed the adapter is level with the base model that has the table over all runs, and
  6.9 points behind in the three later runs. "Not worse" is unproven; the draft now requires a
  non-inferiority test for it.
- Power: at the development effect, 48 tables per model pass the primary gate about 68% of the time and
  96 tables about 91%. The draft protocol now asks for 96.

What the adapter can offer that a cache over the prompt cannot is the table removed: 110 to 200 KB in
place of the table's tokens, and no limit from the context window. The claim with a mechanism behind it is
therefore "table removed, not worse than the base model reading the table", tested against a cached prompt
on size and time, and "more examples than fit in the prompt", which no arm here tests yet.

## State at handoff (2026-11-18 08:00 EST)

Nothing is locked. `protocol_v5_draft.json` awaits an independent review and the owner's pin of an
unseen model. Not built: the cached-prompt comparison. The owner's priority is A1 to A3; B1 uses
the Mac GPU only when no A lane needs it.

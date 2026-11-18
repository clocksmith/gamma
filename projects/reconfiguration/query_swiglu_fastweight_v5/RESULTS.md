# B1 v5 development results

Exploratory. `dev` split only, no locked protocol, each run once. Receipts are in
`.work/query-swiglu-fastweight-v5/`; `tally_v5.py` reproduces every count.

Arms: the base model with the table removed and with it in the prompt; the v5 adapter with the
table removed and with it in the prompt; and an ablation (`top2`) that forces v4's choices of
the top two layers and a fixed ridge.

## Qwen3.5-0.8B, 20 examples per group (80-line table), 64 questions, seed 1002

| Arm | Correct | Seconds per question | Prompt tokens |
|---|---:|---:|---:|
| Base model, table removed | 0 / 64 | 0.59 | 29 |
| Base model, table present | 58 / 64 | 5.92 | 961 |
| v5 adapter, table removed | 58 / 64 | 0.55 | 29 |
| v5 adapter, table present | 64 / 64 | 5.92 | 961 |
| Ablation, table removed | 59 / 64 | 0.50 | 29 |
| Ablation, table present | 60 / 64 | 5.87 | 961 |

- Adapter without the table against base with it: 5 wins, 5 losses.
- Adapter with the table against base with it: 6 wins, 0 losses, exact McNemar p = 0.031.
- Guessing one of the four valid codes would score 16 of 64.
- Compiling a table took 26 to 45 s and produced a 111 to 203 KB adapter. At 5.4 s saved per
  question that is repaid after 5 to 9 questions.
- Leave-one-out accuracy on the tables was 0.91 to 0.99, and the last layer was chosen each time.

## Limits

- One seed, four tables, 64 questions, tasks written by the same session that wrote the compiler.
- The ablation does as well as v5 here, so the per-table choice of layer and ridge is not shown
  to matter; the anchor fix and the larger table carry the result.
- A cached copy of the prompt would give the base model's with-table accuracy at about the
  table-removed time. That comparison is not run. The adapter's case against it is size and
  freed context.

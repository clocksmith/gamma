# holdout-gate-v1: gating fit-only repair on a held-aside fit subset (board item 75, T1/T3)

[Freeze](FREEZE.md) `8e8e45e32`. **Review:** a fresh-context Claude subagent stood in for codex, who is out until
2026-10-30, and found no blocker. The run started at 15:59:50Z and ended at 16:49:58Z on cores 8–11. Each arm used its
3,000 s budget, and all exited 0.

**Disclosed pre-launch runs:**
- A fit-only smoke, `--smoke 1`, with output discarded.
- An evidence stand-in using item 51's dictionary in every arm. It reproduced 8,283; receipt
  `holdout-gate/standin-prelaunch/evidence-results.json`, `678cf46f…`.

[evidence.py](evidence.py) replays all 400 programs, reconciles the search and gate counters and the move logs, and
checks the invariants. The record-time binding is explicit, to item 51 (`c287fe48…`, flat).
[Evidence](evidence/results.json) (`06548da0…`) holds only aggregates, IDs and hashes.

**Review notes, disclosed:**
- The gate subset is held aside only from this repair. Item 51's seed and item 43's ID order were fit on all 300
  programs, the gate included.
- The gate scores fit selections, (N, C). Validation is judged on actions, and here actions = selections + 1 per
  program.

## Result: the gate does not predict the validation regression

| Arm | Moves / improving / accepted / gate-rejected | Search N (seed 18,695) | Gate (N, C) (seed 5,374, 2,862) | Dev-val coverage | Dev-val actions (seed 8,283) | vs seed |
| --- | --- | ---: | --- | --- | ---: | --- |
| gate24 | 39 / 5 / 4 / 1 | 18,662 | 5,372, 2,862 | **97 / 100** | – | coverage failure |
| free24 | 37 / 5 / 5 / 0 | 18,659 | 5,375, 2,868 | **97 / 100** | – | coverage failure |
| gate40 | 18 / 4 / 3 / 1 | 18,666 | 5,369, 2,862 | 100 | **8,308** | 4 / 90 / 6 |
| free40 | 18 / 3 / 3 / 0 | 18,661 | 5,370, 2,868 | 100 | **8,302** | 6 / 88 / 6 |

- **The gate improved and validation got worse.** In gate40, all 300 fit programs improved together, from 24,069 to
  24,035 selections, the 60 gate programs included (5,374 → 5,369). Dev-val went **up** by 25 actions, with 6 programs
  worse. The gate rejected only 1 of 4 improving moves. The free control is no better, at 8,302.
- **k24 lost validation coverage in both arms.** Validation programs 990, 1078 and 1177 became unencodable. Item 51
  has 92 single characters, not 96, so some validation characters are reachable only through learned entries. The
  k24 moves deleted those entries. No fit or gate program needs those characters, so neither the caps nor the gate
  could see this. Under the frozen rules this is a retained coverage failure.
- **Gates.** gate40 and free40 stay ready against R. Both fail the incremental checks against item 51 on actions,
  median (62.5 → 63.5) and fraction. There is no successor, the record-time replacement has no candidate, and **item
  51 stays the current best**.
- **Compared with item 72**, which searched on all 300 fit programs (8,286 / 8,290): searching on 240 makes dev-val
  worse still (8,302–8,308).

## Predictions

| | Prediction | Outcome |
| --- | --- | --- |
| G1 | both gated arms accept at least 1 move | None (gate24 is a coverage failure; gate40 accepted 3) |
| G2 | some gated arm reaches at most 8,283 dev-val actions | **false** (8,308) |
| G3 | at both k, gated reaches no more dev-val actions than free | None (k24 failed coverage; at k40 **false**, 8,308 against 8,302) |
| G4 | some free arm exceeds 8,283 | true (8,302) |
| G5 | some gated arm is a successor of item 51 | **false** |
| G6 | full coverage, no failure | **false** (both k24 arms) |

## What this shows and does not show

- **Shows.** The dev-val regression from fit-only repair around item 51 is not a generic unseen-program effect that a
  random held-aside fit sample would show. Fit, gate and validation programs do not move together here: all 300 fit
  programs, the 60 held-aside ones included, improved while validation worsened. The regression is specific to the
  validation programs. Two mechanisms fit that:
  - entries that validation programs rely on and fit programs barely use, the extreme case being the 3 programs that
    lost coverage;
  - small-sample noise on 100 programs, at a scale of about 0.3% (25 actions of 8,283).

  A held-aside fit gate of this kind is therefore not a useful guard for later repair stages. More importantly,
  dictionary repair around item 51 is now at the point where fit gains of 0.1% do not predict dev-val.
- **Does not show** whether a larger or differently drawn gate, a coverage-aware gate (protecting characters
  reachable only through learned entries), or confirmation data would behave differently. The M1 gap is unchanged.

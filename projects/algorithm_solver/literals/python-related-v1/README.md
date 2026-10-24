# python-related-v1: related (adjacency) removal against random removal for the Python repair (board item 73, T4)

[Freeze](FREEZE.md) `152f24ee8` and [amendment 1](AMENDMENT-1.md) `db9444a1c`: a separate removal rng and idle cores
0, 1, 2 and 4. **Review:** a fresh-context Claude subagent stood in for codex, who is out until 2026-10-30. It found no
code blocker, and its launch-condition blocker (busy cores) and rng note were fixed in the amendment. The run started at
15:08:50Z and ended at 15:23:51Z. Each arm used its 900 s budget, and all exited 0.

**Disclosed pre-launch runs:**
- One evidence stand-in under the amended contract. Each arm carried its unchanged item 69 start dictionary. It
  reproduced 914 and 1,395 actions; receipt `python-related/standin-prelaunch/evidence-results.json`, `978f6325…`.
- An earlier stand-in under the pre-amendment contract is superseded and retained.

[evidence.py](evidence.py):
- verifies the contract first;
- re-evaluates every sealed dictionary independently, equal to the arm's own evaluation;
- evaluates the R, item 31 anchor and start references;
- asserts qualification by exact source hash;
- reconciles every counter with the move logs;
- checks the invariants. No arm failed.

[Evidence](evidence/results.json) (`0addf34b…`) holds only aggregates, IDs and hashes.

## Result: null; related neighbourhoods are almost all solved to optimality and contain no improvement

| Arm | Model | Moves / accepted | Repairs optimal | Fit N / C | Dev-val actions | vs start | vs R |
| --- | --- | --- | --- | --- | ---: | --- | --- |
| w8rel | lex | 33 / 0 | 32 of 33 | 1,925 / 886 | 914 | 0 / 9 / 0 | 3.7% (needs 5%) |
| w8rnd | lex | 61 / 1 | 60 of 61 | 1,924 / 887 | 914 | 0 / 9 / 0 | 3.7% |
| w7rel | lex + ratio row | 40 / 0 | 39 of 40 | 3,617 / 2,513 | 1,395 | 0 / 9 / 0 | 1.8% |
| w7rnd | lex + ratio row | 53 / 0 | 51 of 53 | 3,617 / 2,513 | 1,395 | 0 / 9 / 0 | 1.8% |

- **Related removal accepted nothing at either width.** Nearly every related repair finished with a proven optimum
  (HiGHS status 7). In each of those freed neighbourhoods, with these candidates, the incumbent is therefore already
  lexicographically optimal under the caps.
- **The random control at w8** made the same kind of single −1-selection fit move as item 70's lex arm, with C +1 and
  no validation change. At w7 it accepted nothing.
- **Related arms ran fewer moves** (33 against 61, and 40 against 53). Each related move pays one extra canonical
  encoding, and its repairs took longer.
- **Matched pairs.** Validation is identical, 0 / 9 / 0, at both widths. On fit, w8rel against w8rnd is 0 / 26 / 1,
  the one program w8rnd's move improved. At w7 they are identical.

## Predictions

| | Prediction | Outcome |
| --- | --- | --- |
| P1 | some related arm accepts at least 1 move | **false** |
| P2 | some related arm reaches fewer validation actions than its start | **false** |
| P3 | at both widths, related reaches no more validation actions than random | true (equal) |
| P4 | at both widths, related ends at a strictly lower fit objective than random | **false** |
| P5 | no arm ready against R | true |

## What this shows and does not show

- **Shows.** Item 69's best Python dictionaries admit no lexicographic improvement in any of the 71 related and 111
  random neighbourhoods solved to optimality here, apart from the one −1 move. These were k = 48 at w8 and k = 8 at
  w7, under per-program caps, with the freed entries plus 4,000 candidates. Together with item 70, freeing more
  entries at random or along adjacency at these sizes does not find validation gains from item 69's dictionaries.
- **Does not show** a local optimum for any larger neighbourhood, other candidate sets, or uncapped moves. A move that
  makes some fit program worse, for example, is excluded by design. It also does not show that the R gap (at least 13
  actions at w8, at least 46 at w7) cannot be closed by a source-side change or a different objective. Nothing here
  touches the JS M1-GAP rows.

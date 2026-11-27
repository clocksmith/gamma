# closure-holdout-v1 results

Preregistered at `96423fc63` (rules, dictionaries, selection and scoring scripts). The scorer, a separate session that
did not build the arms, drew the new sets and scored everything; its log is [SCORER-LOG.md](SCORER-LOG.md) and its
commit is `f24954812`. Numbers below are from [out/results.json](out/results.json).

## Decision rules

All seven held.

| Id | Rule | Outcome |
| --- | --- | --- |
| S | `closed` at least 1.0% fewer tokens than `token` on `fresh2` at 4,096, sign p < 0.05 | holds: −8.47%, 181 lower, 15 higher, p = 2.3e-37 |
| O | `closed` at least 1.0% fewer than `bpe` on `fresh2` at 4,096, sign p < 0.05 | holds: −1.24%, 127 lower, 53 higher, p = 3.4e-8 |
| P | `token` at least 1.0% fewer than `closed` on `fresh2` at 256, sign p < 0.05 | holds: `closed` +13.36%, 200 higher, p = 1.2e-60 |
| F | single-byte share of `closed` below `token` on `fresh2` at 4,096 | holds: 23.9% against 34.0% |
| G | `closed` no more tokens than `bpe` at every grid size on `fresh2` | holds |
| J-python | `closed` at least 1.0% fewer than `token` on TheAlgorithms/Python at 4,096 | holds: −18.29%, 199 lower, 1 higher |
| J-javascript | same on ramda/ramda | holds: −17.28%, 200 lower, 0 higher |

## Tokens relative to BPE at the same size

| Set | Status | 84: token | 84: closed | 3,924: token | 3,924: closed | 3,924: closed vs token |
| --- | --- | --- | --- | --- | --- | --- |
| fresh2 (200 problems) | new | −12.13% | −0.39% | +7.90% | −1.24% | −8.47% |
| TheAlgorithms/Python (200 files) | new | +7.30% | +0.92% | +21.34% | −0.85% | −18.29% |
| ramda/ramda (200 files) | new | +5.52% | +0.52% | +19.25% | −1.36% | −17.28% |
| fresh (objective-holdout-v1 test) | used | −12.34% | −0.38% | +7.75% | −1.22% | −8.32% |
| Express (objective-holdout-v1 test) | used | +5.11% | −0.50% | +19.87% | −1.09% | −17.48% |
| dev | used | −11.87% | −0.34% | +6.40% | −1.45% | −7.38% |
| train | used | −13.09% | −0.44% | −22.01% | −2.61% | +24.87% |

## What this says

- The objective-holdout-v1 reversal is a structure effect. With the token-gain objective fixed, adding BPE's closure
  turns a 7.9% deficit against BPE at 3,924 fragments into a 1.2% lead on new CodeNet problems, and an 19 to 21% deficit
  into a 0.9 to 1.4% lead on two new repositories.
- Under closure the exact objective beats BPE at 3,924 fragments on every set (0.9 to 1.4% off the training files) and
  never loses to BPE on the `fresh2` grid. The gain is small.
- Open selection's lead with 84 fragments holds on CodeNet only. On all three repositories `closed` beats `token` at
  every grid size, and BPE is slightly ahead of `closed` at 84 fragments on the two new ones (0.5% and 0.9%, under the
  1.0% threshold, but on more files than not).
- Mechanism: from 2,000 fragments on, `token` leaves 34 to 35% of `fresh2` tokens as single bytes (55 to 56% and 57 to
  58% on the repositories) whatever its size; `closed` falls from 29% to 24% on `fresh2`, as BPE does.

## Limits

One 259,706-byte training corpus, one exact parser, token counts only. The scorer and builder are separate sessions of
the same model family under one author, so this is a preregistered holdout, not an independent replication. Standard
BPE merge replay, larger training sets and other closure notions (for example prefix closure) were not tested.

## Post hoc, after scoring: the attribution to closure does not survive

Computed on the already-scored sets, so nothing here is preregistered. Scripts: `explore_rivals.py` (`out/posthoc-rivals.json`)
and a scoring of the frozen `codenet-replication-v1/chains/primary` chains (same training split, same parser, 3,924 fragments).
Tokens relative to 16-byte BPE:

| Rule | fresh2 | Express | TheAlgorithms/Python | ramda/ramda | train |
| --- | --- | --- | --- | --- | --- |
| token gain, open (L=16) | +7.9% | +19.9% | +21.3% | +19.2% | −22.0% |
| closed token gain | −1.2% | −1.1% | −0.9% | −1.4% | −2.6% |
| GreedTok (frozen chain, L=16) | +8.1% | +22.2% | +19.2% | +18.7% | −19.3% |
| PathPiece (frozen chain, L=16) | +5.6% | +21.2% | +23.0% | +18.0% | −13.3% |
| greedy-byte, open (gain per stored byte) | −0.7% | +2.5% | −1.0% | −0.8% | −6.7% |
| greedy-byte, open, two-problem support | −2.7% | +0.3% | −2.6% | −1.0% | −1.0% |
| token gain, open, two-problem support | −2.9% | +5.7% | +4.1% | +5.2% | −6.2% |
| closed token gain, two-problem support | −2.8% | −2.2% | −0.8% | −1.6% | +0.2% |

Token gain against BPE at the same length limit on fresh2: +2.0% (L=8), +7.9% (L=16), +17.7% (L=32).

- Closure does not hold the objective fixed. If w = uv with u, v in the dictionary, replacing each use of w by u, v
  costs one token per use, so a closed candidate's exact gain is at most its number of uses; an open candidate can save
  up to |w| − 1 per use. Closure therefore also removes token gain's length leverage, and the two are confounded in the
  `closed` arm.
- An open rule without that leverage (greedy-byte) removes most of the reversal, and with two-problem support beats
  `closed` on fresh2 and TheAlgorithms/Python. Its single-byte share is below `closed` on every set, so the fallback
  plateau is not specific to closure.
- Every open rule that maximizes raw token count reverses, including GreedTok and PathPiece.
- `closed` keeps the best result on Express and ramda/ramda (two JavaScript repositories); whether that residual is a
  closure effect is untested.
- The greedy engines use lazy (Minoux) evaluation. Exact token gain under shortest-path parsing is not submodular, so the
  chains are lazy-greedy orders, not guaranteed exact argmax at every step; the size of any divergence is unaudited.

## Post hoc trainer audit

`audit_lazy.c` replays each lazy trainer, checks that it reproduces the frozen chain entry for entry (both do), and at
every 400th step recomputes the exact gain of every candidate whose provable bound could beat the lazy pick.
`verify_greedy.c` checks a given chain against brute force without using the trainer's selection code.

| Chain | Steps checked | Lazy pick not the best | Example |
| --- | --- | --- | --- |
| `token` (frozen, also objective-holdout-v1's arm) | 10 (`out/audit-lazy-token.tsv`) | 9 (every check from step 400 on) | step 2,000: picked gain 10, best 21 |
| `closed` (frozen) | 10 (`out/audit-lazy-closed.tsv`); 20 (`out/verify-lazy-closed.tsv`) | 9; 18 | step 400: picked gain 78; `.map(` had gain 90 under a stale key of 68 |

Both chains are lazy-greedy orders, not exact greedy orders. The frozen dictionaries and every token count measured on
them are unaffected; any statement about what exact greedy token gain would select is not supported by them.
`engine_exact.c` keys the heap by a bound that never rises (each use of w saves at most the tokens currently needed to
spell w, minus one); exact chains are being trained and are not yet part of any result.

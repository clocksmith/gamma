# Amendment 1, 2026-10-24: separate removal rng, idle cores, and one wording fix (before launch)

Nothing has launched. A fresh-context Claude subagent reviewed the freeze `152f24ee8`, standing in for codex, who is
out until 2026-10-30. It found no code blocker and one launch-condition blocker.

1. **Cores.** Cores 12–15 were busy with another session's jobs pinned to cores 12–31. mpstat showed them 27–71% idle,
   while cores 0–7 were 51–95% idle. Both the 900 s arm budget and HiGHS's 120 s limit are wall-clock, so contention
   would give the arms unequal compute and contaminate P3 and P4. The arms move to cores **0, 1, 2 and 4**, the four most
   idle at the check; core 3 was 51% idle. These are codex's cores, and codex is out until 2026-10-30. The launcher runs
   under `taskset -c 0,1,2,4`.
2. **A separate removal rng.** The related arm drew |learned| + 1 values per move from the shared LNS rng. That shifted
   the random-candidate sample and every later draw relative to the random control, so P3 and P4 would have mixed the
   removal rule with sampling noise. Both arms now draw their removal from **one dedicated rng,
   `random.Random(1010)`**: the related rule in the related arms, `sample` in the controls. The shared rng (seed 10)
   now only draws the 1,000 random candidates, the same number per move in every arm, so its stream is identical across
   matched arms. HiGHS's `random_seed` stays 10.
3. **Wording.** FREEZE.md's "the only changes from item 70" omits one change. Item 70 paired ratio against lex within
   each width. Here both w8 arms run item 69's lex model and both w7 arms run item 69's ratio model, as the arms table
   shows. The matched comparison is removal rule only.

The reviewer's minor notes are kept as limits. The related arms do one extra canonical encode of the 27 fit texts per
move, so slightly fewer moves fit in 900 s. An empty learned set would raise an error, which these seeds cannot reach.
The evidence-level warm/feasible assert aborts the whole evidence run rather than one arm.

The 8 tests pass. The stand-in is re-run under this contract. No arm, budget, gate or prediction changes. This file is
added to the contract.

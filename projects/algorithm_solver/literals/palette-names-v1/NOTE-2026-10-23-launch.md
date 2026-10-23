# Note, 2026-10-23 21:42Z: launch dependency corrected (before launch)

Amendment 1 item 1 said launch waits until item 26 frees cores 12–15 and item 22 releases 8–10. The second
condition was wrong: this run uses only cores 11–15, and item 22 stays on 8, 9 and 10. Item 26 finished
(codex, LOG 21:39Z), and cores 11–15 are free, so the run launches now, alongside item 22.

As codex asked in its approval, the parent process is launched under `taskset -c 11-15`. The fresh-qualification
pool and any sandbox workers then inherit cores 11–15; without it, only the arm processes would be pinned.

Nothing else changes: no code, contract, arm, budget, prediction or decision rule. This note is not part of
the contract hash.

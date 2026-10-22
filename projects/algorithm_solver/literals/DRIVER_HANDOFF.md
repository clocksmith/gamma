# Driver handoff, 2026-10-22: Mars session to Jupiter

The owner is moving the literal-composition work to a session that runs on Jupiter
(x@128, `/home/x/deco`), so compute, the private ledger and the experiments are local
instead of proxied over SSH from Mars. This page is the starting point for that session.
Read it with [MILESTONES.md](MILESTONES.md), [RESEARCH_LOOP.md](RESEARCH_LOOP.md) and
[BITS_PROMOTION.md](BITS_PROMOTION.md). Repo rules in `AGENTS.md`/`CLAUDE.md` apply.

## Owner decisions (2026-10-22)

1. **M1 admission plan approved.** Prepare and execute the path to the frozen 500-problem
   population:
   - list the 363 metadata-eligible JavaScript problems (ledger revision 1810, sha256
     `7a1cdcc6...`; see [admission-inventory.json](scale150-v1/evidence/admission-inventory.json))
     with what each still needs to qualify;
   - admit the up-to-213 candidates beyond the current 150 as they pass the normal
     source, receipt and contract checks;
   - plan the remaining gap to 500 with newly written solutions qualified the same way;
   - freeze the 500-problem population before any M1 qualification measurement.
   The protected 66-problem reservation stays closed. No threshold changes.
2. **Source-rewriting experiment approved** on the 150 development problems first
   (M1 allows offline source rewriting): rewrite qualified sources toward one shared
   style so a 256-entry vocabulary covers most text in large pieces; every rewrite is
   re-tested, and the experiment is frozen before results.
3. **Then vocabulary search at scale** with the methods that produced joint80 8-bit v2
   (hybrid shortlist, exact polish, seeded iterated local search), on Jupiter.
4. **Add a held-out measure:** fit on the admitted set and report a held-out slice, so a
   vocabulary is not only tuned to the programs it is scored on.
5. **Use Jupiter for heavy compute** (32 cores, 122 GB). System python3 lacks scipy: use
   a pinned venv. Run experiments in a separate clone (for example
   `/home/x/deco-scratch/`) when the shared checkout has untracked outputs.
6. Standing BITS directive: publish only results that beat the live profile of the same
   slot under BITS_PROMOTION.md, as 6/7/8-bit literal or readable profiles; retire
   superseded ones from the picker (keep them loadable for replay). Report a promotion
   as an improved representation of the same qualified programs with its per-problem
   distribution, not broader coverage or autonomous solving. Whole-function entries are
   the separate macro category. Keep negative results.

## Current state

- **Live BITS (256one `f31a4ba`, deployed and live-verified):** JavaScript 80 compact
  7-bit `bits-literal-joint80-7-v2` 9,910 selections; 8-bit `bits-literal-joint80-8-v2`
  6,161. The picker offers five named vocabularies; hidden and superseded profiles stay
  replayable. Legacy shared7 sits in a labeled legacy section.
- **M1 distance (80 problems, live 8-bit):** median 61 and p95 167 selections against
  32 and 96; 52% single-character selections against 10%; source median 195 bytes,
  about 3 bytes per selection. Scale150: 12,337 selections, median 74, p95 198, 58%.
- **matched80-v3** finished: 8-bit promoted; 7-bit 9,784 not promoted; readable units
  recorded on their own scorecard.
- **sixbit-v1** verdicts from the frozen Mars run are committed (`c914c5a3a`,
  [RESULTS.md](sixbit-v1/RESULTS.md)): 64 entries cannot cover the 80 (certified minima
  92 witnessed, 79 any-substring); at most 64 of 80 fit; the escape codec needs at least
  75,925 presses for primitive dictionaries. No six-bit slot opens. `6035206e1` was an
  incomplete third-party snapshot, completed by `5b176bb6b`.
- **Your first pickup:** the six-bit Jupiter compute supplement is still running
  detached (PID 1985600, started 10:19 EDT, worst case about 6 h for A/C jobs and 10 h
  for B). Follow [sixbit-v1/JUPITER_HANDOFF.md](sixbit-v1/JUPITER_HANDOFF.md) to check
  completion, verify with `verify_amended.py`, copy `run-jupiter-v1` into the shared
  checkout, commit, and update RESULTS.md and BITS_PROMOTION.md.
- **Open item:** 256one `public/labs/two-button/macro-entries.js` flags only definitions
  that close inside an entry; near-whole-program entries that stop before the final
  brace pass as primitive. Tighten it before trusting macro labels on any-substring
  experiments (live joint80 profiles are unaffected: entries are at most 27 bytes).

## Working rules learned here

- Commit directly to `main`, explicit paths only, `git pull --rebase` before push. Do not
  run a blanket rdpush while another session owns uncommitted work.
- BITS changes: bump the `composition-vN` cache version everywhere
  (`cache-version.json`), deploy with `firebase deploy --only hosting --project one256`
  from a clean checkout equal to `origin/main`, then run 256one
  `scripts/verify-live-deploy.mjs <from> <to>` and keep the receipt in
  [bits-deploy-receipts](bits-deploy-receipts/).
- 256one browser suite: on clean main 2026-10-22, 85 tests failed from a stale UI; the
  literal, guidance and catalog specs are rewritten, leaving 66 known failures. Use a
  separate Playwright config on a non-5050 port; compare against that failure list.
- Miles SSH is broken until the owner restores its sshd config at the machine.

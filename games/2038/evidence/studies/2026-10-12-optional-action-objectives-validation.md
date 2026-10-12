# Candidate validation and positional diagnostics — 2026-10-12

Applies to the user-selected 0.25.0 / engine 0.28.0 / rules 0.14.0-rc.6-test candidate. The [matched comparison receipt](2026-10-12-optional-action-objectives-results.md) owns the 0.24.4 comparison and its hypotheses, source limits, and raw hashes. This additional receipt records validation of the final sealed executable and a clean committed unified audit. All game outcomes here are simulations, not human playtests.

## Executable acceptance

- Clean source commit: `37ddab33bc1c56e578e851d7647fdaa66c5af12a`, based on `aba758ac6f4b6eb597856c553d91d3d157d9e884`. This receipt is an evidence-only successor; it does not rewrite the audited source identity.
- Runtime: Node 24.19.0, npm 11.9.0, Linux. No dependency installation, provider calls, paid LLMs, or model downloads were needed.
- `npm test -- --test-isolation=none`: 304 passed, zero failed/cancelled/skipped. This executes the complete suite using Node’s supported no-process-isolation mode.
- Required default `npm test`: 299 passed, 5 failed. The five unified-matrix worker-launch failures are `ERR_WORKER_INVALID_EXEC_ARGV`: this executor injects process-only Node flags into the child test runtime, and the existing worker launcher forwards those flags to worker threads. The same failure was reproduced on untouched 0.24.4. These failures remain reported; the project test command and worker infrastructure were not weakened or changed.
- Focused `node --test tests/movement-objectives-candidate.test.mjs`: 46 passed, including affordable skips for all six factions and six Actions; unaffordable movement; ordinary and Research movement exactly once; destination lock; preserved equipment/Production and Organize reassignment; twelve-turn skipped games; objective-seed invariance and all-four visibility; rich/batch turn accounting.
- `npm run build:all`, `npm run gallery:baseline`, `npm run check`, `npm run game:release:verify`, and `git diff --check`: passed. Generated files were rebuilt through their supported owners.
- `npm run publish:firebase:build`: local public-package build passed for six HTML surfaces. This command only built files; it did not deploy them.
- Root `python -m py_compile gamma.py`: passed. No Python game/engine files were changed.
- Sealed old releases, 82 cards, 153 components, Research cost of two Compute, all other prices/yields, faction abilities, lore, and Initiative rotation remain unchanged. No control-income system was added.

## Browser qualification and publication state at this receipt

Browser harnesses were adapted to the movement-first interface. A DOM-adapter walkthrough reached 48 decisions and twelve moves, exercised affordable and unaffordable skips, and reached two Training decision checks. This is a JavaScript/DOM-adapter check, not a real-browser qualification.

Real-browser validation is blocked in this environment: installed Chromium cannot create its process-singleton socket, and the separate supported cloud browser cannot reach the executor-local server (connection refused). The server was verified from its own execution session. No public tunnel or deployment was created. Real-browser screenshots, responsive layout, and end-to-end interaction remain unverified.

The source is committed locally. At receipt creation, push and exact-pushed-SHA CI verification are still blocked pending supported authenticated Git access. No remote branch/ref was changed. The connector tree-write path returned HTTP 422 `GitRPC::SymlinkDisallowed` while preserving pre-existing root symlinks; unrelated symlinks were not altered. Later publication status must be reported against the actual pushed SHA, not inferred from this local receipt.

## Clean-source unified audit

Command, from `games/2038`:

```bash
npm run simulate:audit -- --runs 480 --initial-runs 1 --batch-size 2 --workers 2 --seed mandate-20261012-candidate-audit-v1 --pre-registration-id 2026-10-12-optional-action-objectives-audit --output evidence/studies/simulation/2026-10-12-candidate-audit.json
```

The first launch was interrupted by an execution approval-review cancellation before producing a report. A single authorized retry of the same command completed with exit code zero and the result below. This interruption is not counted as a game failure or an additional sample.

- Seed: `mandate-20261012-candidate-audit-v1`.
- Registration fingerprint: `sha256:22c82fbd3fbb0c8f847d721016d0aafd0c70629e881a27cd45c5d112ca1c261f`; settings were locked before results. The audit uses the existing committed matrix and balance contracts.
- Final source commit is the clean commit above (`sourceDirty: false`); final engine fingerprint is `sha256:394851dc15d295b18ad7565fb0dbe8514b7265ba22792d651248b4ee22dbb7a8`.
- 480 games: 410 canonical matrix games across 168 registered cells, plus 70 bounded adversarial diagnostic games. Matrix coverage: 56 three-player, 154 four-player, 200 five-player games.
- Seven unchanged authored profiles; fixed/variable objectives; homogeneous weighted/greedy and both alternating weighted/greedy backend regimes. No rule overlay or control income. This audit covers the canonical candidate only; the separate matched study supplies the isolated-change contrasts.
- The 410 matrix games have zero reported integrity violations, policy fallbacks, forced no-ops, or blocked-after-commitment turns. These rollups are assembled before the adversarial slice; the 70 completed adversarial games have no archived integrity rollup. Partial pooling and multiplicity-adjusted confidence sequences were calculated.
- The adversarial slice used two candidates and two runs per candidate; its status is `diagnostic_not_balance_authority`. It does not establish a competent best response or absence of exploits.
- Stopped at the registered 480-game bound. `precisionReached: false`; maximum core half-width 0.5 versus target 0.12. No statistically qualified dominance was detected, but these wide intervals cannot establish equivalence or balance.
- **Balance result: `outside_provisional_bounds`, promotion ineligible.** The six failed descriptive checks are recorded below. Exit zero means the audit completed, not that its balance gates passed. No threshold was relaxed and no additional experiment was selected to seek a passing result.

| Check | Observed range | Existing maximum |
| --- | ---: | ---: |
| `canonical:p3:seat_win_share_range` | 26.786 pp | 10 pp |
| `canonical:p3:faction_win_share_range` | 26.786 pp | 15 pp |
| `canonical:p3:profile_win_share_range` | 29.167 pp | 18 pp |
| `canonical:p4:seat_win_share_range` | 18.831 pp | 10 pp |
| `canonical:p4:profile_win_share_range` | 19.140 pp | 18 pp |
| `canonical:p5:seat_win_share_range` | 10.500 pp | 10 pp |

These sparse, adaptively allocated mixed-policy margins are diagnostics, not causal estimates of seat advantage. In particular, they must not be substituted for the identical-policy common-seed seat comparison below. The raw report retains `trackedReceipt: false` and `humanApproval: false`, reflecting launch-time metadata. This later receipt does not rewrite those fields or confer balance-promotion approval.

- Raw report: `evidence/studies/simulation/2026-10-12-candidate-audit.json` (ignored local archive).
- Report SHA-256: `20c4e67da0d2bac4ba0a7fdac08c75c4db59937081cde06e431d4c72746c398b`.

## Production and final scoring by seat

This table is derived from the existing matched-study raw files, with no new simulations. All seats use `balanced_operator`; fixed and variable objectives are pooled. Factions are circularly rotated as registered. Counts are 36, 48, and 60 matched scenarios per backend for three, four, and five players. Compute is realized Production per player per Era after resource-cap clipping. Mandate is final score after Era IV Production, Reputation Review, AGI recognition, and all four final objectives. Each value is baseline 0.24.4 → combined candidate. Seats are zero-based.

| Players / backend | Seat | Realized Compute Production | Final Mandate |
| --- | ---: | ---: | ---: |
| 3 / greedy | 0 | 3.611 → 3.201 | 16.944 → 15.389 |
| 3 / greedy | 1 | 3.785 → 3.632 | 16.278 → 16.278 |
| 3 / greedy | 2 | 3.493 → 3.556 | 16.694 → 16.611 |
| 3 / weighted | 0 | 1.840 → 2.326 | 14.250 → 14.028 |
| 3 / weighted | 1 | 1.875 → 1.826 | 13.000 → 14.000 |
| 3 / weighted | 2 | 2.090 → 1.889 | 14.472 → 12.722 |
| 4 / greedy | 0 | 3.292 → 3.609 | 16.854 → 17.458 |
| 4 / greedy | 1 | 3.568 → 3.844 | 17.312 → 17.917 |
| 4 / greedy | 2 | 3.677 → 3.792 | 15.729 → 17.229 |
| 4 / greedy | 3 | 3.708 → 3.729 | 18.417 → 17.500 |
| 4 / weighted | 0 | 1.984 → 2.276 | 13.333 → 12.833 |
| 4 / weighted | 1 | 1.776 → 1.984 | 13.583 → 12.229 |
| 4 / weighted | 2 | 1.917 → 1.995 | 12.188 → 12.771 |
| 4 / weighted | 3 | 1.974 → 2.125 | 12.833 → 12.958 |
| 5 / greedy | 0 | 3.958 → 3.454 | 17.033 → 16.933 |
| 5 / greedy | 1 | 3.633 → 3.796 | 17.317 → 16.500 |
| 5 / greedy | 2 | 3.346 → 3.671 | 17.067 → 16.833 |
| 5 / greedy | 3 | 3.312 → 3.625 | 16.200 → 16.450 |
| 5 / greedy | 4 | 3.417 → 3.604 | 16.317 → 17.033 |
| 5 / weighted | 0 | 1.879 → 2.046 | 13.917 → 13.733 |
| 5 / weighted | 1 | 1.908 → 1.750 | 12.700 → 12.567 |
| 5 / weighted | 2 | 1.658 → 2.025 | 12.767 → 13.200 |
| 5 / weighted | 3 | 2.150 → 2.179 | 13.667 → 13.300 |
| 5 / weighted | 4 | 2.321 → 2.200 | 13.900 → 12.300 |

Initiative at Production is unchanged: starting from seat zero before the first Headline, the Era I–IV Initiative seats are `[0, 0, 0, 0]` for three players, `[3, 2, 1, 0]` for four, and `[3, 1, 4, 2]` for five. The table exposes positional outcomes without changing that rule. It does not demonstrate that Initiative caused a particular score or production difference.

No balance promotion, human usability conclusion, production deployment, retail publication, or future control-income implementation is supported by this receipt.

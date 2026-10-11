# Shared-hex economy and physical-state repair — 2026-10-10

User request: fix the simplified game and balance it. Preserve twelve turns,
shared hexes, all lore, six Actions, and push-your-luck Training. No writing.

## Baseline and exploratory selection

Baseline source: `223c73d0b`, executable 0.24.2 / rules 0.14.0-rc.3-test.
The clean-source unified audit ran 960 games with seed
`shared-hex-balance-20261010-baseline`, 3/4/5 players, registered weighted/greedy
backend regimes, all six institutions and authored personas, variable/fixed
objectives, plus its bounded adversarial slice. Zero integrity failures; observed
balance is outside provisional bounds. Four-player faction win-share spread:
0.150658; profile spread: 0.247335. Seats, openings and winning-path diversity
passed their observed bounds. These aggregate margins are not a causal faction
ranking or qualified dominance claim.

An exploratory 432-game opening study was followed by 3,456 matched games:
3/4/5 players × 2 seed blocks × 6 faction rotations × all focal seats × 6 openings
× 4 one-lever arms. Openings: adaptive, recruit twice, equip twice, Research twice,
Deploy twice, Influence twice, where legal. All then use the same public-state
heuristic. It neither sees hidden deck order nor represents optimal play.

Candidate arms: unchanged; Organize yields 1 Compute instead of 1 Runway;
Organize yields 2 Runway; sole objective winners receive 3 instead of 2.
Recruit-first winner credit was 3.47%, 17.36%, 6.25%, and 4.17% respectively.
The Compute candidate merits confirmation; the other changes are not selected.

Fresh-seed confirmation: 1,728 games, same rotations/openings and only unchanged
versus Compute arms. Seed prefix `heldout-20261011`, disjoint from selection
`opening-20261010`. Recruit-first credit improved 6.25% → 16.67%, mean score
20.84 → 23.27. Equipment remained 23.96%; Research 25.69% → 28.47%.
No conclusion about human balance follows. Influence-first remains weak in this
heuristic. Mixed player counts must also be inspected separately.

Raw JSON, exact study scripts (including their absolute local import paths), and
the reproduced policy failure are retained locally under
`evidence/studies/simulation/shared-hex-20261010/`. Hashes below bind those files.

## Registered independent matrix confirmation

Before choosing the canonical production change, run a clean committed source
through `simulate:audit`, 1,920 matches, 3/4/5 players, same registered default
personas/backends and objective modes, seed `shared-hex-20261011-confirmation`.
Two paired arms: canonical Runway versus `organizeProduction: compute`.
No threshold changes. Compare faction/seat/profile ranges, opening/path diversity,
forced no-ops and integrity separately by supported count. Preserve unfavorable
results. Improved recruit-first performance alone cannot qualify the change.

## Implementation deltas and audited surfaces

- Physical/rules: remove pencil. Existing identity-card orientation encodes AGI;
  its edge pointer encodes final score without disturbing holdings or Org positions.
  82 cards, 153 items. Print A5 mats, both identity faces and score ticks.
- Policy: reproduce/fix the accepted Research/Deploy treatment's reads of removed
  facilities/projects. Use public Orgs, destinations and Reputation instead.
  Complete-game regressions cover 2/3/4/5 players.
- Engine: recruitment reads its owning configured cost rather than hard-coded 2;
  experimental production overlay affects all three Organize hexes.
- CLI: `--help`, unknown options and missing values cannot start experiments.
- Browser: identity recognition is visible; game state remains owned by the match.
- Canonical production, faction starts/abilities, deck composition, Action prices,
  scoring and Training: unchanged pending the paired matrix.
- Lore: no change. Historical sealed releases and raw evidence: no change.
- Reference/player aids: generated from the updated rules/configuration; no new aid.
- Tests: policy/CLI/config regressions and physical output checks, plus existing
  full source and browser checks. No manufactured or human-playtest claim.

## Raw-file SHA-256

- `current-policy-before.log`: `2e684e3408c54296bfb30de4ef7a41c24c46516f1abe7b4eeec219a981b40e77`
- `hex-candidate-study.mjs`: `490c3572502b5447aa1986a332a514f0e06531a1b9db7e4b90c9b460b1ef798d`
- `hex-heldout-study.mjs`: `716c60537061ba53febb9ed5373971179e76f79b940f45f095bad21a93a20025`
- `hex-opening-candidates.json`: `19491dd59be98c1d2a363af96dc8b0ed22e7200584ffef72f1b1e7087b323302`
- `hex-opening-heldout.json`: `7fb89cc64afe76a5969f1fe343879f9025c39867055ba1473e537d3cff523246`
- `hex-opening-results.json`: `39bc69d490ff315e8799bd78b92a228dffcc67033401bef8da56de29546ad33b`
- `hex-opening-study.mjs`: `9c1f019be01107ab306e7e6d7caf7890c7f3d3f09984a1d7a390f5b5acb31594`
- `mandate-balance-baseline.json`: `d2b8bbeef2b176d2c22450bb0d07dd0d5bd9236610fe65c296560587522830ee` (automatic simulation archive also retained).

## Execution amendment before a result — larger batches

The first paired matrix was stopped during adaptive sampling after initial
coverage; no final result or numerical selection was accepted. Its progress log
is retained locally as `/tmp/hex-matrix-interrupted.log`. Repeated two-game
batch setup dominated runtime. Restart with explicit `--batch-size 24`, the same
1,920-match ceiling, paired seed `shared-hex-20261011-confirmation`, four workers,
all registered axes and unchanged thresholds. Batch allocation is therefore
amended before examining final outcomes; the interrupted run is not evidence.

The repaired policy regression now passes all supported counts plus exploratory
two-player play. The 225-test run had 224 passes and one source-identity failure
because external workspace sync created `95823e180` during execution. The failed
worker-determinism test passed unchanged when rerun against that stable commit.
Browser desktop/mobile complete games passed without page errors. A print check
confirmed A5 mats and 63 × 88 mm identity cards without overflow. Pointer centering,
full turn reference and the remaining card/token print dimensions were then refined.

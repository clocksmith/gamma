# Release identity correction — 2026-07-31

## Scope

This receipt corrects release attribution only. It changes no game rule, player
profile, simulation result, or archived report.

## Issue

The two reports below were produced while canonical content and runtime files
had changed but `data/game-version.json` still declared executable `0.8.23`.
They therefore record the migrated ruleset fingerprint
`sha256:566df3a53efcb0c093e7397a2fb28a0f153928ba800350e11a1c4273598f93fd`
under `0.8.23`, whose immutable manifest instead records
`sha256:9efa959dbfbaebb23f4985872e148f0122b60ec31ff43a8957be0f7e2b31cb46`.

- `20260731T230206857Z-tournament-0-8-23-566df3a53efc-codex-personas-3p-full-progress-20260731-1x3-cli.json`
- `20260731T233955860Z-tournament-0-8-23-566df3a53efc-codex-personas-4p-full-progress-20260731-1x4-cli.json`

Their recorded engine fingerprints also do not match a single immutable
release artifact. The reports must not be relabeled as `0.8.24`: a later
release cannot retroactively make a dirty-tree engine reproducible.

## Disposition

- The raw reports remain unchanged.
- Treat both reports as descriptive historical evidence only; exclude them
  from exact comparisons, balance promotion, and rules-change selection.
- `versions/0.8.23/` and `versions/0.5.0-rc.24-test/` retain their original
  bytes.
- `0.8.24` and `0.5.0-rc.25-test` are newly generated snapshots for the live
  tree after the source reorganization. New reports may use those identities.

## Verification

- `git diff --quiet -- versions/0.8.23 versions/0.5.0-rc.24-test`
- `npm run game:release:verify`
- `npm test`

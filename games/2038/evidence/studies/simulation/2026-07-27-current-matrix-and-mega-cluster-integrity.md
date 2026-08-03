# Current matrix and Mega-Cluster integrity receipt

Date: 2026-07-27  
Evidence label: simulation plus targeted diagnostic  
Verdict: Foundry signal retained as a hypothesis; balance promotion blocked by
an integrity defect; simulator repaired before the registered one-lever probe

## Identity

All three reports used source commit
`15a40a490f2d75126506c3da290d793f366d5c44`, executable `0.6.2`,
physical candidate `0.4.0-rc.9-test`, engine `selected-rules` `0.8.2`,
coverage `lean-grid-ready-v6`, and clean source.

| Report | Runs | SHA-256 |
| --- | ---: | --- |
| `20260727T171846360Z-unified-matrix-audit-0-6-2-22a9423143ca-m3t4-unified-matrix-20260727-current-2000x4-unified-matrix-cli.json` | 2,000 | `da089aba4f6dd0b22e59aa9c0e5051f3d3182b9fdc1e77977d4c9338df8db08b` |
| `20260727T172045347Z-tournament-0-6-2-22a9423143ca-foundry-diagnostic-greedy-20260727-500x6-cli.json` | 500 | `71afd6e9fad4cf9cb9dccd680c79c23e11cbed9ca4d79cfb3c9304808f9b23bd` |
| `20260727T172110467Z-tournament-0-6-2-22a9423143ca-foundry-diagnostic-weighted-20260727-500x6-cli.json` | 500 | `7f16645bb54bc6ca859ba369628d5d9b061d11dc88ee8aa3530618f6b9e71aca` |

Raw JSON remains local ignored evidence. This receipt is the tracked
interpretation.

## Matrix result

The unified report contains 1,930 matrix matches and 70 bounded adversarial
matches across player counts 2–6, fixed and variable Mandates, every authored
persona, balanced faction and seat rotation, and weighted and greedy backends.

- Status: `credible_dominance_detected`.
- Credible cell:
  `playerCount=6|factionId=foundry|backendId=greedy`.
- Exposure: `228`.
- Raw win share: `56.14%`, against an expected `16.67%`.
- Empirical-Bayes interval: `49.30%–62.08%`.
- Multiplicity-safe confidence sequence: `33.87%–78.41%`.
- Credible pairwise-dominance cells: `0`.
- Credible cyclic metas: `0`.
- Declarations: `1 / 1,930`.
- Emergent-cooperation rate: `34.46%`.
- Betrayal rate: `1.14%`.
- Causal suppliers finishing competitively: `62.45%` across `261`
  observations.
- Policy fallbacks: `0`.

The signal is interaction-specific, not a claim that Foundry always wins. The
registered precision target was not reached.

## Integrity defect and disposition

The all-greedy six-player diagnostic had no numeric-state violation. The
all-weighted diagnostic found two states with `Compute = -1`, at matches 399
and 414. Replay inspection identified one exact boundary:

1. a joint Mega-Cluster was legal when selected;
2. its partner spent Compute during an earlier simultaneous resolution; and
3. the later acceptance path charged the stale contribution anyway.

Executable `0.6.3` revalidated both participants’ complete Runway and Compute
contributions at acceptance. An exact 500-game rerun from clean commit
`41cea3f` retained the same two failures; its raw report is
`20260727T173041081Z-tournament-0-6-3-b29a3c5e9490-foundry-diagnostic-weighted-20260727-500x6-cli.json`
with SHA-256
`e47152b2e842da21be303e905ca86042a37d631985afdd86bf3eedef002bc5d0`.
That falsified the first diagnosis as complete.

The remaining defect was Agent Swarm’s second Core Action: the engine selected
a legal Cloud Research or Consumer Deploy while its destination discount still
applied, then removed that discount after selection. A zero-Compute player
could consequently pay one. Executable `0.6.4` suppresses the second
destination bonus before affordability filtering. Regressions now cover both
the stale joint contribution and the compound-action discount boundary.

The 2,000-run balance result is not discarded: its Foundry cell remains a
diagnostic hypothesis. It cannot authorize a rule change because a subsequent
targeted cohort exposed an executable correctness defect.

## Registered one-lever follow-up

The preregistered paired probe is:
`preregistrations/foundry-starting-compute-three.json`.

It compares the canonical Foundry starting Compute of `4` with `3`, using the
same root seeds and every other rule unchanged. Shovels was rejected as the
probe lever because the all-greedy diagnostic recorded mean Shovels income of
exactly `0`; changing it would not address the observed greedy interaction.

The first 3,000-match execution of that file produced
`20260727T173616625Z-unified-matrix-audit-0-6-4-826b443e1290-m3t4-foundry-compute-ab-20260727-3000x4-unified-matrix-cli.json`
with SHA-256
`0f54bd75d3ce61152f6edae53f92cad923e7b9141e6499adad6e2f62d1af8ee2`.
It is not an A/B result: the runner pooled both rules configurations inside
the same inference cells and included the configuration id in each random
seed, so the arms were neither separated nor common-random-number pairs.
Its general Foundry signal remains descriptive; no lever effect is inferred.

Executable `0.6.5` makes the rules configuration explicit in every inference
family and pairwise cell, gives paired cells identical seeds and rotations,
allocates adaptive batches to both arms together, reports per-configuration
outcomes and bounded paired deltas, and promotes any nested tournament
integrity violation to an `invalid_integrity` verdict.

The corrected common-seed rerun produced
`20260727T174330534Z-unified-matrix-audit-0-6-5-ac35773c895a-m3t4-foundry-compute-ab-20260727-v2-2998x4-unified-matrix-cli.json`
with SHA-256
`66112a33ea623d01eefe5e6dd6fa4da9a3504e087d394679ab1874276c4cd76f`.
It contains 1,464 matched pairs per arm, no unmatched pairs, no standing
mismatches, and no integrity violation. Lowering Foundry starting Compute from
4 to 3 changed its overall paired win share by `-0.008799` and mean score by
`-0.120`; the bounded interval for win-share delta was `[-0.115, 0.098]`.
Both arms produced 4 declarations in 1,464 matrix matches. The probe therefore
does not distinguish the value from noise and does not support promotion.

The stronger surviving hypothesis is player-count-scaled Foundry value:
canonical Foundry raw win share rose from `0.485` at two players to `0.398`,
`0.383`, and `0.332` at four, five, and six players, against expected shares
of `0.500`, `0.250`, `0.200`, and `0.167`. Foundry with the greedy backend was
especially high at four through six players (`0.615`, `0.574`, `0.491`).
Executable `0.6.6` therefore preregisters two separate one-lever probes:
Round III New Architecture Compute `3 → 2`, and Round IV Everybody Gets a GPU
scoring from 1 Mandate per 2 rivals to 1 per 4. Neither is canonical unless a
clean common-seed result supports it and the user approves it.

The first 11,998-match confirmation attempt produced
`20260727T180533580Z-unified-matrix-audit-0-6-6-376586876c40-m3t4-foundry-scaling-confirmation-20260727-11998x4-unified-matrix-cli.json`
with SHA-256
`0cc0a7ff4c094e798bc648a2e1cb927a08577f4c97d9316d058b8dd8293abb7a`.
Its verdict is `invalid_integrity`, not balance evidence. One three-player
common-seed match in every arm ended with an unpowered-Facility penalty taking
a zero-Mandate player to `-1`, contrary to the global nonnegative-track
contract. The identical failure in all arms proves the defect is independent
of the Foundry probes. Executable `0.6.7` clamps final Mandate after offline
penalties at zero and adds a direct regression. No rule-probe conclusion uses
the invalid report.

The clean confirmation rerun from commit `51240df` produced
`20260727T181929266Z-unified-matrix-audit-0-6-7-74e48d44072f-m3t4-foundry-scaling-confirmation-20260727-11998x4-unified-matrix-cli.json`
with SHA-256
`853be69d542b41eb97380e2229a55cf1a546cef60e4e6525feab58aafeaecb84`
and zero integrity violations. Its selected and rejected rule conclusions are
owned by `2026-07-27-foundry-scaling-rule-selection.md`.

## Surface audit

- Canonical physical rule: the later selection changes only Everybody Gets a
  GPU scoring from per two rivals to per four.
- Semantic graph: Foundry starting Compute and Shovels frequency now have
  explicit shared values; rendered player text is unchanged.
- Machine-readable data: regenerated from the graph.
- Simulator: joint-project payment revalidation added; Foundry starting
  Compute and Shovels limit exposed through the canonical rules variant.
- Interactive game: accepts the same explicit rules overlay as headless runs.
- Tests: stale joint-payment regression and Foundry-overlay regression added.
- UI and reference cards: no player-facing mechanic changed.
- Versioning after selection: executable `0.7.0`, engine `0.9.0`,
  synchronized physical candidate `0.4.0-rc.15-test`.
- Promotion boundary: the GPU divisor is promoted by the clean confirmation
  and explicit user authorization; all other probed values remain unchanged.

## Later Shovels correction

That promotion boundary was withdrawn after the
`2026-07-27-foundry-shovels-executable-correction.md` receipt demonstrated
that executable `0.7.0` did not apply Shovels to qualifying Wild Actions.
Executable `0.7.1` corrects the trigger and requires fresh Foundry evidence.

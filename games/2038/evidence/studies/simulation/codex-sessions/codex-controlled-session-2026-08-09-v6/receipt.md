# Codex controlled-session receipt

Session: `codex-controlled-session-2026-08-09-v6`

Evidence: **complete but non-promotable LLM simulation diagnostic**, not a human physical or blind playtest

Rules: `0.7.0-rc.3-test`  
Executable: `0.10.2`  
Ruleset: `sha256:092fa7b149dd7630ce7ca5760b3aef8a54c680297e8bad65a94456a9661ff8b0`  
Release boundary: `149a99be3c21cff71abf3ac734a927ae4f35d2d3`  
Physical kit: `0.7.0-rc.3-test-b14f223f`  
Physical-kit fingerprint: `sha256:fbdbf77732a6ed2e5d9ddd954d90d3f0712b9e395d366dc73fc931525188fb4a`  
Harness source: `ab878cc2951cec320bf201ec86ddf0855707e903`

## Recorded path

- Emulated unboxing and component sorting: 4 participant records.
- Independent source-chunk reading across all four frozen Default Game documents: 44 records.
- Cross-document rules synthesis: 4 participant records.
- Initial participant questions: 32.
- Source-grounded facilitator answers: 32.
- Remaining follow-up questions: 16.
- Final ready/no-blocker confirmations: 0. All four participants remained
  `readyToPlay: false`; the v6 harness proceeded after facilitation without a
  second readiness check.
- Complete Codex gameplay decisions: 255.
- Postgame winner, World Ending, and rules reconstruction: 4 records.

## Outcome

| Rank | Faction | Mandate | Declared AGI |
| ---: | --- | ---: | --- |
| 1 | Mirevanta Works | 23 | no |
| 2 | Loopfold AI | 12 | no |
| 3 | Kestralyn | 12 | no |
| 4 | Corthaven | 2 | no |

World Ending: **The Plural Future**

## Artifact integrity

- `session.json`: `sha256:59c6c47280e86a6ad71cc5c12a0e28ac5f90529d8c9d2203442131dd2809e26d`
- `gameplay-report.json`: `sha256:cad5875deb938f1d58253ff63f6b339b04a760fe8b138288057159fb51d78508`
- Provider fallback count: 0
- Rules and engine identity remained frozen through report completion.
- Gameplay provenance recorded `sourceDirty: true` because the v6 CLI created
  this in-repository output directory before gameplay captured launch identity.

## Disposition

The complete outcome is retained as diagnostic evidence, but it is not the
clean controlled-session receipt. The successor must write its live journal
outside the repository and must fail closed unless every participant records
`readyToPlay: true` with zero blocking questions after final facilitation.

## Interpretation boundary

- This is LLM simulation evidence, not a facilitated or blind human playtest.
- Unboxing and rules reading are text-grounded emulations without physical handling.
- Provider duration is machine latency and cannot estimate human setup, teaching, or play duration.
- One match cannot establish balance, complexity weight, teachability, or comparative provider quality.

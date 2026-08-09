# Codex controlled-session receipt

Session: `codex-controlled-session-2026-08-09-v10`

Evidence: **LLM simulation**, not a human physical or blind playtest

Rules: `0.7.0-rc.3-test`  
Executable: `0.10.2`  
Ruleset: `sha256:092fa7b149dd7630ce7ca5760b3aef8a54c680297e8bad65a94456a9661ff8b0`  
Release boundary: `149a99be3c21cff71abf3ac734a927ae4f35d2d3`  
Physical kit: `0.7.0-rc.3-test-b14f223f`  
Physical-kit fingerprint: `sha256:fbdbf77732a6ed2e5d9ddd954d90d3f0712b9e395d366dc73fc931525188fb4a`  
Harness source: `e2853c2785a448e372bd2e136fbdf125e8278ab4`

## Recorded path

- Emulated unboxing and component sorting: 4 participant records.
- Independent source-chunk reading across all four frozen Default Game documents: 44 records.
- Cross-document rules synthesis: 4 participant records.
- Initial participant questions: 32.
- Source-grounded facilitator answers: 32.
- Remaining follow-up questions: 16.
- Final ready/no-blocker confirmations: 4.
- Complete Codex gameplay decisions: 248.
- Postgame winner, World Ending, and rules reconstruction: 4 records.

## Outcome

| Rank | Faction | Mandate | Declared AGI |
| ---: | --- | ---: | --- |
| 1 | Mirevanta Works | 19 | no |
| 2 | Loopfold AI | 15 | no |
| 3 | Corthaven | 11 | no |
| 4 | Kestralyn | 8 | no |

World Ending: **The Plural Future**

## Artifact integrity

- `session.json`: `sha256:1fe2dcde21f4036e184b42efc847ef0fea840bb44a1ae8e777983dbdfd3282b9`
- `gameplay-report.json`: `sha256:ef7686ebe27e28c9d28054044bb9407393987b13ec3b6544e526e47f6ded532e`
- Gameplay source provenance: clean commit `e2853c2785a448e372bd2e136fbdf125e8278ab4`.
- Final readiness: four of four participants ready, with zero blocking questions.
- Provider fallback count: 0
- Gameplay integrity violations: 0.
- Pre-play provider retries: two five-minute Map Reference timeouts for Loopfold; attempt 3 succeeded.
- Forced no-ops: 1. Mirevanta selected `declare_agi` in Era IV cycle 3 despite having zero Facilities; resolution rejected the impossible escalation explicitly. The simulator intentionally exposes every unused Action or Escalation and labels current resolvability, so this is a product decision about whether impossible selections should remain permitted—not an AGI declaration or hidden fallback.
- Recorded Power trades: 1; it was not causally necessary to the final result.
- Rules and engine identity remained frozen through report completion.

## Interpretation boundary

- This is LLM simulation evidence, not a facilitated or blind human playtest.
- Unboxing and rules reading are text-grounded emulations without physical handling.
- Provider duration is machine latency and cannot estimate human setup, teaching, or play duration.
- One match cannot establish balance, complexity weight, teachability, or comparative provider quality.

## Diagnostic signals for discussion

- The top two finishers built zero Facilities. Mirevanta scored 19 through Capability, Customers, Trust, and Mandates; Loopfold scored 15 through the same broad lane. Infrastructure enabled Kestralyn and Corthaven but did not convert as efficiently into score in this match.
- The match recorded 62 negotiation or promise-state entries but only one completed Power trade, which was not causally necessary to the result. Every postgame reconstruction described the promise lifecycle as difficult to follow.
- No player declared AGI. The market leaders lacked Facilities, while the infrastructure leaders lacked the combined Capability, Customer, and Grid-Ready requirements.
- The blocked `declare_agi` selection confused multiple postgame reconstructions: some described selection as a declaration even though the authoritative outcome records zero declarations and zero qualifying declarers.
- Mirevanta led after Era I and remained the winner. This is a catch-up diagnostic only; one deterministic LLM match cannot establish leader persistence or runaway scoring.

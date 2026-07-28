# Local Simulation Archive

The Node Simulation Lab automatically saves every completed tournament,
strategy-evolution run, rule search, unified evidence matrix, historical
adversarial diagnostic, and preregistered LLM holdout here.

Generated JSON reports are intentionally ignored by Git because sampled
replays can make them large. Promote a specific result into a dated,
reviewed study only when its configuration and interpretation are worth
preserving in version control.

Report schema 6 embeds the semantic game version, exact ruleset and playtest-kit
fingerprints, engine fingerprint, rule-variant fingerprint, strategy
fingerprint, balance-contract fingerprint and evaluation, RNG contract, and
source Git state. Unified reports also preserve the preregistration,
matrix-contract fingerprint, adaptive allocations, uncertainty families, and
negotiation outcomes. LLM reports preserve their committed plan, CLI/model
provenance, prompt hashes, cache status, and fallbacks. Failed provider calls
also preserve attempted provider/model/request identity, prompt hash, exit
code, duration, and stderr hash beside the fallback. A report without those
fields is legacy evidence: it may be migrated for viewing, but it is not
silently treated as comparable to a versioned report.

Every simulation-driven implementation or rules change requires a tracked
dated Markdown receipt beside the raw report. The receipt must identify the
report hash, results, validity boundary, selected or rejected hypothesis,
exact changes, and the audited rulebook/data/simulator/UI/reference/test
surfaces.

Preregistration documents live under `preregistrations/` and must be committed
before a metered holdout executes. A fresh capture uses write-only cache mode;
its paired reproducibility plan uses read-only mode and fails on a missing
entry. Generated decision caches and raw JSON reports remain local evidence,
not source content.

Deterministic one-lever probes are preregistered in the same directory before
execution. `foundry-starting-compute-three.json` and
`foundry-multiplayer-scaling-probes.json` preserve the hypotheses tested on
2026-07-27. Their disposition is recorded in the tracked Foundry receipts;
the preregistration files are historical experiment plans, not current rules.
`foundry-shovels-once-per-round.json` exposed an executable trigger defect; its
first report is invalid for balance and retained through the dated correction
receipt.

`supported-player-count-baseline-v1.json` is the first current-product matrix
restricted to three, four, and five players. It treats four as the balance
authority and three/five as mandatory regression guards; historical two- and
six-player seeds cannot select a correction for this candidate.

`faction-strength-probes-v1.json` preregisters direct one-lever price and
discount probes selected from the clean paired faction diagnostic. Its
Scientific Method and Industrial Velocity arms are independent; neither is a
physical rule unless a later receipt and explicit approval promote it.

`faction-progress-conversion-v1.json` follows the rejected resource-strength
probe with two independent victory-progress levers: a one-Capability cost when
Scientific Method actually protects a run, and one Mandate when Industrial
Velocity actually discounts a Build. Both remain simulation-only candidates.

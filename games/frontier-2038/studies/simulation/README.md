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
The dated calibration receipt rejects the Capability penalty on both evidence
and faction-truth grounds and nominates the Industrial Velocity Mandate for a
fresh-seed confirmation; neither changes the physical rules.

`faction-public-validation-confirmation-v1.json` preregisters that fresh
confirmation. Its Demis arm preserves all Capability and tests only whether a
Scientific Method rescue receives one fewer threshold Mandate; its independent
Elon arm repeats the realized-discount Mandate on fresh common seeds. Paired
reports must include placement movement as well as win share and score.

The dated confirmation receipt rejects the exact Demis value as too weak and
confirms the Elon candidate on fresh seeds. Confirmation is not physical
promotion: the canonical semantic graph and rulebook remain unchanged until
explicit approval.

`foundry-supported-count-conversion-v1.json` isolates the five-player-only
Mandate on Everybody Gets a GPU. It also requires configuration-specific
player-count summaries and faction-specific Mandate sources so a visible
five-player discontinuity cannot be mistaken for the entire Foundry main
effect.

The dated
[`Foundry supported-count conversion`](2026-07-28-foundry-supported-count-conversion.md)
receipt rejects removing that Mandate as a standalone correction. The point
changes five-player Foundry win share and placement, but Foundry's three- and
four-player strength exists without it. The receipt retains the supplier
identity and requires the next hypothesis to move victory conversion toward
realized rival demand.

`faction-demand-validation-v1.json` independently tests two identity-safe
bottlenecks. The Demis arm adds two Scrutiny only when Scientific Method
actually saves a run and never removes Capability. The Foundry arm retains
four starting Compute and a three-Compute New Architecture ceiling, but grants
one base Compute plus one per accepted rival license. Both arms require exact
configuration-specific faction standings by supported player count.

Its first launch executed zero matches: the matrix rejected the Foundry
formula because three scalar overlay fields violated the one-lever contract.
`faction-demand-validation-v1-restart.json` supersedes it with the same
ability formula represented as one structured lever, retires the unused seed,
and preregisters a fresh replacement seed.

The dated
[`faction demand-validation`](2026-07-28-faction-demand-validation.md)
receipt rejects both exact candidates. Two Scrutiny barely moves Demis and is
not a binding public-validation cost. Demand-coupled New Architecture moves
Jensen in the intended direction while preserving every rival transaction,
but one unconditional base Compute plus accepted licenses is too weak. The
next eligible probes remain prestige conversion for Demis and a stronger
license-only self-Compute formula for Jensen; canonical physical rules are
unchanged.

`faction-prestige-demand-v1.json` preregisters those two independent
continuations. Demis's arm reduces Nobel Effect from two Trust to one while
leaving every scientific output untouched. Jensen's arm removes New
Architecture's unconditional base Compute and retains one self-Compute per
accepted license, every rival transaction, and the three-Compute ceiling.
Neither arm includes the confirmed Elon candidate, so every focal effect
remains isolated.

The dated
[`faction prestige-and-demand`](2026-07-28-faction-prestige-demand.md)
receipt rejects the Nobel reduction: the trigger is too rare to move Demis.
It selects license-only New Architecture for combined-package confirmation.
That candidate preserves every rival sale and payment while moving Foundry to
`30.18%`, `24.82%`, and `22.79%` partially pooled win share at three, four,
and five players.

`demis-late-validation-v1.json` follows the rejected Scientific Method,
Scrutiny, and Nobel candidates with one direct public-validation lever.
Capability 9 and 12 remain fully achieved, but each scores Demis one Mandate
instead of two. The probe leaves starting Compute, Research reliability,
Capability, and every other faction program untouched.

The dated
[`Demis late public-validation`](2026-07-28-demis-late-validation.md)
receipt finds a strong but count-dependent effect. One Mandate at both late
thresholds places Demis among the leaders at three and four players but below
the viable band at five, where late thresholds occur more often. The exact
scalar rule is rejected; a registered follow-up may restore Capability 12's
second point when four rivals provide broad independent validation.

`demis-peer-validation-v1.json` preregisters that refinement as one structured
validation schedule. Capability 9 and 12 score one Mandate for Demis; at five
players only, four rival institutions restore Capability 12's canonical
second point. The schedule changes no technical output.

The dated
[`Demis peer-validation refinement`](2026-07-28-demis-peer-validation.md)
receipt selects that schedule for combined-package confirmation. It moves
Demis to `42.38%`, `26.82%`, and `19.20%` partially pooled win share at three,
four, and five players while preserving Research and Capability realization.
It is not yet a physical rule.

`selected-faction-conversion-package-v1.json` preregisters the first
package-interaction audit. It combines only three independently evidenced
levers: Demis peer validation, Elon realized Industrial Velocity Mandate, and
Jensen license-only New Architecture allocation. The runner records this as an
interaction validation rather than a one-lever causal probe.

Its first clean run is descriptive only because the report omitted the
preregistered action- and winning-path-diversity diagnostics. The fresh restart
added those fields and completed `11,998` clean matches. The dated
[`selected faction-conversion package`](2026-07-28-selected-faction-conversion-package.md)
receipt selects the package for explicit physical-rule approval: four-player
faction spread is `9.28` percentage points, all supported counts remain below
the provisional `15`-point faction bound, no registered dominance appears,
and Build/Research choice does not collapse. Overall balance remains
uncertified because registered precision is incomplete and winning-path
entropy remains below its provisional floor at four and five players.

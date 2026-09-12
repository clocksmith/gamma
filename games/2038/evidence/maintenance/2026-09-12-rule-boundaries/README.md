# Mandate rule-boundary repairs

Baseline: `990d147a8ffd2e631779de2e9da46870ade9c93b`, clean source before edits.
The retained baseline observations below came from the actual imported
`SelectedRulesMatch` through `createInteractiveGame`, with four players and
seed `rule-audit-20260912`. They were deterministic boundary fixtures with
explicit decision choices, not method transcriptions or complete playtests.

| Boundary | Baseline observation | Required result |
| --- | --- | --- |
| Project at Compute Estate, 3 Runway / 0 Compute | No affordable offer | Offer and charge 3 / 0 |
| Project at Fabrication Corridor, 2 Runway / 1 Compute | No affordable offer | Offer and charge 2 / 1 |
| Resource exchange before a Capability-blocked Deploy | No offer; completion rejected | Exchange independently; retain blocked-action warning |
| The Dead Remain on Shift, full Scrutiny, 0 Runway / 3 Trust, Allocation Exchange | Ends at 1 Runway / 3 Trust in normal play's queued-penalty mode | Pay Trust before production; end at 2 / 2 |
| Benchmark Leak before a duplicate, full Scrutiny and 1 Runway | Both Research paths permit Scientific Method | Leak consumes the Runway; the duplicate crashes |
| Joint Venture after a legal relocation co-locates its hosts | Still adds one contract resource | Contract remains owned but yields nothing |

The engine repair uses one complete Build-cost calculation and one adjacency
predicate. Automatic Scrutiny penalties settle when added. Training results
retain ordered permanent effects; interactive Research applies those effects
before the next decision, and banking does not apply them a second time.
The fixed one-for-one exchange, caps, offer window, and explicit acceptance
remain the selected rules.

The compiler derives project names in `newThisEra` from project unlock records.
Build-risk copy references the common project cost, and connection instructions
include Fusion. Canonical rules clarify Capability, Trust, Research duplicates,
exchange independence, and overflow fallback. Selected Headline and historical
lore now explain existing effects without adding asset transfers, retired powers,
or a different exchange rate. Headline effects and Era placement are unchanged.

Focused regressions are in `tests/rule-boundaries.test.mjs`. Existing general
infrastructure fixtures use districts without discounts when testing the common
base price. The older overflow test now asserts the immediate state.

Validation commands and their captured outputs:

```sh
npm run build:all
node --test tests/rule-boundaries.test.mjs tests/gameplay-audit.test.mjs tests/infrastructure-progression.test.mjs tests/rules-review.test.mjs tests/engine.test.mjs
npm test
npm run check
git diff --check -- games/2038
```

## Validation results

- `build.log`: content, documentation, and gallery generation passed.
- `focused-tests.log`: all 54 focused tests passed.
- `compatibility-tests.log`: all three legacy-payment and revised-prose regressions passed.
- `full-tests-final.log`: all 329 tests passed, with no failures or skips.
- `project-check.log`: authoring, provenance, generated-content, and project checks passed.
- `git diff --check -- games/2038`: passed without output after the code corrections.

`full-tests.log` retains the first unsuccessful full run: two assertions required
the deliberately revised prose, one aggregate Training-result fixture exposed
the missing legacy Scientific Method payment, and five server tests could not
bind localhost ports inside the sandbox. A simulation also rejected its launch
identity because the payment correction changed engine source during that run.
The final full run used localhost permissions and held source fixed throughout.
Historical prose assertions now allow the specifically requested revisions,
and legacy aggregate Training results still pay for consumed Scientific Method.

Source and contract checks do not establish browser behavior, numerical balance,
or a human playtest.
No publication or deployment is part of this repair, and historical release
bundles retain their original bytes.

Component: Mandate 2038 rules, simulation, Training engine, and content compiler.
Intent: preserved.
Acceptance evidence: baseline observations, focused regressions, and captured check logs.
Boundary effects: action legality/payment, Research effect order, Venture operation,
and generated player instructions and selected lore.

## Retained output receipts, 2026-09-12

The source review of `6938d662` found that Gamma's global `*.log` ignore rule
excluded the captured outputs from the published acceptance directory. The six
original files survived locally. The project ignore rules now explicitly allow
these six receipts to be included in the next commit and push; their bytes have
not been changed or replaced with a reconstructed run.

[Receipt index and SHA-256 checksums](receipts.json) records byte lengths,
reported results, and provenance limits for each file:

| Original output | Historical result |
| --- | --- |
| [Build](build.log) | Content, docs, and gallery generation completed |
| [Focused regression tests](focused-tests.log) | 54 passed, 0 failed |
| [Compatibility tests](compatibility-tests.log) | 3 passed, 0 failed |
| [Initial full-suite attempt](full-tests.log) | 320 passed, 9 failed; retained, not acceptance |
| [Final full-suite run](full-tests-final.log) | 329 passed, 0 failed |
| [Project checks](project-check.log) | Content and project checks completed |

The original logs carry the old `0.20.4` executable label where npm prints a
package version. They do not embed a contemporaneous commit and complete tested
source-tree fingerprint. The independently reviewed commit `6938d662` is a
review reference, not a retroactively proven historical test identity. These
checksums bind the retained output bytes, not those outputs to an immutable
release. No test was rerun during this packaging repair.

Release preparation remains open: declare a new identity under the semantic
version rules in `docs/playtesting-and-evidence.md`, generate new executable and
physical-candidate artifacts without overwriting historical versions, and
exercise the four scenarios through the browser with that identity captured.
The current September 8 declaration must not stand in for a sealed September 12
release. Receipt packaging changes no mechanics and performs no deployment.

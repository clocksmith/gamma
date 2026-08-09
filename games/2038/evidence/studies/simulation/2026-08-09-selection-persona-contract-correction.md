# Selection, trade, and persona contract correction

**Evidence class:** deterministic simulation diagnostic and executable defect
correction; not a balance promotion or human playtest  
**Baseline source:** `844b7df9c96d74aec12d7ed4ff6a9d178f5b6c03`, clean  
**Candidate:** executable `0.11.0`, rules candidate `0.7.0-rc.4-test`, engine
`0.13.0`  
**Authoritative player count:** four

## Trigger and hypothesis

The complete v10 Codex session selected Declare AGI with zero Facilities. The
choice appeared in a legal packet even though no movement, payment, target, or
trade could satisfy the missing Facility and Grid-Ready requirements. Inspection
then exposed a second mismatch: the simulator described zero-resolution choices
as recoverable by immediate trade, but its offer generator rejected every offer
while the selected Action had zero resolutions before that trade. It also chose
post-Act offers from pre-Act resources. Finally, `partnerWeights` and
`spatialPreference` were validated and fingerprinted persona fields that no
deterministic policy executed.

The correction hypothesis is narrow: legal selection should retain real
simultaneous commitment risk while excluding impossible commitments; a choice
may remain selectable when one accepted pre-Act trade could make it legal.
Deterministic policies should execute every declared preference and report the
resulting trade dependency explicitly.

## Frozen runs

The primary comparison arms used four players, batch projection, 64 matches,
four workers, eight matches per chunk, two sampled replays, and no provider
calls. The clean release also includes 32-match three- and five-player integrity
guards because those player counts remain supported.

| Arm | Seed and roster | Raw report | SHA-256 | Provenance |
| --- | --- | --- | --- | --- |
| Baseline weighted | `selection-contract-sweep-v1`; Capability Rusher, Infrastructure Compounder, Power Broker, Market Maximalist; all weighted | `2026-08-09-selection-contract-sweep-v1.baseline-weighted.raw.json` | `38e52f38e44829fd9e447c869cd04581390fc984227c25a32b78cb3c9e6e4237` | clean baseline |
| Rejected calibration | same | `2026-08-09-selection-contract-sweep-v1.candidate-dirty-weighted.raw.json` | `7b5bb7d9486406e3b7c8ae7363f37854249e22277267e92455f622031f6c37e2` | dirty diagnostic |
| Selected calibration | same | `2026-08-09-selection-contract-sweep-v1.candidate2-dirty-weighted.raw.json` | `03f00471a123a0beaca140dff07449b96a013db354a00a87093f439691b71575` | dirty diagnostic |
| Persona exercise | `persona-contract-sweep-v1`; AGI Candidate, Power Broker, Balanced Operator, Trust Governor; all greedy | `2026-08-09-persona-contract-sweep-v1.candidate-dirty-greedy.raw.json` | `b1b999f13871b248c3c9e3a240efd4afe86b47121c26b45755da8904e306fdef` | dirty diagnostic |
| Clean weighted repeat | `selection-contract-sweep-v1`; same roster as baseline; all weighted | `2026-08-09-selection-contract-sweep-v1.candidate-clean-weighted.raw.json` | `1f3989def2b80807c6f65ba6d8af4bf5ff392d506e871833636577f449247933` | clean `c689143b` |
| Clean persona repeat | `persona-contract-sweep-v1`; same roster as persona exercise; all greedy | `2026-08-09-persona-contract-sweep-v1.candidate-clean-greedy.raw.json` | `6779feb6959bcba06040796abb4e1ba9fb3cc439ea8e08154aeb120f6254a1bf` | clean `c689143b` |
| Three-player guard | `selection-contract-sweep-v1-p3`; Capability Rusher, Infrastructure Compounder, Power Broker; all weighted | `2026-08-09-selection-contract-sweep-v1.candidate-clean-p3.raw.json` | `10fea171e168fd314acb6fc2058231d216ec1bb5c379e7fd4217269b73408199` | clean `c689143b` |
| Five-player guard | `selection-contract-sweep-v1-p5`; Capability Rusher, Infrastructure Compounder, Power Broker, Market Maximalist, Balanced Operator; all weighted | `2026-08-09-selection-contract-sweep-v1.candidate-clean-p5.raw.json` | `e8438537c61405f1c3aa546efc2fe2f9de3bb92416fd861af8640b80e7b43865` | clean `c689143b` |

The local archive also contains the timestamped copies emitted automatically by
the CLI. Dirty candidate rows calibrate implementation only and cannot qualify
the release. Every clean report names the full source commit
`c689143b3b2cf456d58b3d05c22b224837b9349a` and records `sourceDirty: false`.

## Results

The clean baseline produced 57 forced no-ops in 3,072 ordinary opportunities
(`1.855%`). The first candidate weighting treated trade dependency too
optimistically: 180 selections required trade, only 32 were accepted, and 190
commitments blocked (`6.185%`). That calibration was rejected.

The selected `0.02` trade-dependency multiplier produced six trade-required
selections, four offers, zero acceptances, 61 forced no-ops (`1.986%`), and no
integrity violation or fallback. The close baseline/candidate no-op totals do
not prove improvement; the correction's verified gain is semantic: impossible
choices are absent and remaining blocks have an attributable cause.

The greedy persona exercise produced two blocked commitments (`0.065%`) and no
fallback. AGI Candidate averaged exactly three Facilities, 8.516 Capability,
2.969 Customers, and 0.328 Power purchases, but no player reached a legal
declaration window. That is an AGI-route gap, not evidence for another rules
change. The run must not be described as balance evidence.

## Implemented deltas and surface audit

- **Rulebook:** clarified empty starting Facility supply, selection eligibility,
  rejected required trades, and selection-versus-resolution for Declare AGI.
- **Player aid:** states the same eligibility test.
- **Machine-readable rules:** no costs, rewards, decks, factions, or numeric
  balance values changed.
- **Simulator:** filters impossible selections, proves complete provisional
  exchanges without side effects, generates post-Act offers after Act, retains
  later target/rejection blocks, and records trade-required outcomes.
- **Deterministic and CLI runners:** receive the same legal set and status; rich,
  batch, inline, and worker paths retain exact parity.
- **Personas:** added explicit resource values; preferred partner and placement
  fields now affect deterministic scoring and are exposed to CLI prompts.
- **Browser:** no separate rules implementation changed; browser-native opponents
  use the shared environment and policy modules.
- **Schemas and tests:** profile schema, policy tests, selection tests, trade
  timing tests, packet-ceiling tests, and deterministic parity checks updated.
- **Physical components:** no piece count or component form changed.
- **Playtest protocol:** advanced to the new synchronized candidate and preserves
  teachability, duration, negotiation quality, and balance as unmeasured.

## Validity boundary

These sweeps test executable consistency and deterministic policy behavior.
They do not establish human willingness to attempt trade-dependent Actions,
the social meaning of a rejected rescue trade, balance, duration, teachability,
or whether the AGI route is satisfying. No gameplay number was promoted from
these runs. The next physical session must use the exact rc.4 kit and record
every unavailable choice, required trade, rejection, and post-reveal block.

## Clean release repeats

The exact weighted and persona seeds were repeated after the implementation was
committed. Their aggregate diagnostics are byte-for-byte consistent with the
selected dirty calibration reports: the weighted run recorded 61 forced no-ops,
six trade-required selections, four required offers, zero acceptances, four
required-trade failures, 44 other post-commitment blocks, zero integrity
violations, and zero policy fallbacks. The greedy persona run recorded two
forced no-ops, no trade-required selection, zero integrity violations, and zero
policy fallbacks.

The supported-count guards also completed without integrity violations or policy
fallbacks. The three-player guard recorded 28 forced no-ops, three
trade-required selections, three offers, and no acceptances. The five-player
guard recorded 58 forced no-ops, 15 trade-required selections, 15 offers, and
six acceptances. The five-player result proves that an accepted enabling trade
can execute through the repaired selection contract; it does not establish that
the frequency or terms of such trades are balanced for human play.

All four clean runs reported zero legal AGI windows. Seat, faction, and AGI
alerts remain diagnostic warnings. The release evidence therefore closes the
selection, deterministic-runner, and declared-persona execution defects, while
leaving AGI viability, faction balance, negotiation quality, duration, and
teachability open for controlled physical play.

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

All runs used four players, batch projection, 64 matches, four workers, eight
matches per chunk, two sampled replays, and no provider calls.

| Arm | Seed and roster | Raw report | SHA-256 | Provenance |
| --- | --- | --- | --- | --- |
| Baseline weighted | `selection-contract-sweep-v1`; Capability Rusher, Infrastructure Compounder, Power Broker, Market Maximalist; all weighted | `2026-08-09-selection-contract-sweep-v1.baseline-weighted.raw.json` | `38e52f38e44829fd9e447c869cd04581390fc984227c25a32b78cb3c9e6e4237` | clean baseline |
| Rejected calibration | same | `2026-08-09-selection-contract-sweep-v1.candidate-dirty-weighted.raw.json` | `7b5bb7d9486406e3b7c8ae7363f37854249e22277267e92455f622031f6c37e2` | dirty diagnostic |
| Selected calibration | same | `2026-08-09-selection-contract-sweep-v1.candidate2-dirty-weighted.raw.json` | `03f00471a123a0beaca140dff07449b96a013db354a00a87093f439691b71575` | dirty diagnostic |
| Persona exercise | `persona-contract-sweep-v1`; AGI Candidate, Power Broker, Balanced Operator, Trust Governor; all greedy | `2026-08-09-persona-contract-sweep-v1.candidate-dirty-greedy.raw.json` | `b1b999f13871b248c3c9e3a240efd4afe86b47121c26b45755da8904e306fdef` | dirty diagnostic |

The local archive also contains the timestamped copies emitted automatically by
the CLI. Dirty candidate rows calibrate implementation only and cannot qualify
the release. Clean post-commit repeats are recorded below when available.

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

Pending the clean implementation commit. This section must name exact report
hashes and source provenance before the study is treated as complete release
evidence.

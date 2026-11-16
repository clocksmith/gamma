# Rejected fixed-gate AGI Mandate coda diagnostic

**Evidence class:** deterministic simulation diagnostic and executable
consistency proof; not balance evidence or a human playtest  
**Candidate:** executable `0.12.0`, rules candidate `0.7.0-rc.5-test`, engine
`0.14.0`  
**Ruleset fingerprint:**
`sha256:3d43ed4c86e88914cd58b97fffab55e432a769f6beaec0447c0bc723e360cddb`  
**Authoritative player count:** four

**Disposition:** rejected after implementation. The fixed five-percent gate
and all-player selection do not express the selected product intent. The
retained result is evidence about the superseded `0.12.0` / rc.5 mechanism,
not authority for the next candidate.

## Frozen rule

After the Era IV Mandate scores and offline-Facility penalties, the ordinary
winner under the printed tie breakers is provisional. One shared roll opens the
AGI coda with probability `500 / 10,000`. If it stays closed, the provisional
result stands. If it opens, each player's effective Mandate is final Mandate
plus three for a registered claim. Normalized fourth-power effective Mandate
weights select one institution, which declares AGI and becomes the sole winner.
An all-zero field uses equal weights.

Declare AGI is an Era IV claim action. It requires Capability six, costs three
Compute, and adds three Scrutiny. It does not score Mandate, declare AGI, end
play, or condition the five-percent gate.

## Correctness and surface audit

The implementation uses final Mandate after the offline-Facility penalty, not
the pre-penalty public track. The provisional winner uses the same Mandate,
Trust, Customer, Compute, and joint-victory tie contract as ordinary final
scoring. The AGI personhood or property Headline resolves only after selection
and before the World Ending.

The authored rules, card copy, world companion, physical inventory, component
specification, browser copy, deterministic personas, simulation description,
and release manifests now agree on claim cost, timing, card face, five-percent
gate, claim bonus, fourth-power weights, sole-winner override, and World Ending.
No current authored surface retains the superseded Customer, Facility,
Grid-Ready, Trust, Capability-nine, or qualified-declarer requirement. The AGI
Blog Post lowers Capability from six to five for its cycle.

The complete suite passed `212/212` tests. Content build/check, content
boundaries, semantic validation, numeric-provenance lint, project validation,
release creation, and release verification also passed.

## Clean runs

All runs used batch projection, four workers, eight-game chunks, two sampled
replays, deterministic local policies, and no provider calls.

| Field | Seed and population | Games | AGI | Overrides | Selected ranks | Claims / selected claimants | Raw SHA-256 |
| --- | --- | ---: | ---: | ---: | --- | ---: | --- |
| p3 weighted | `agi-mandate-coda-v1-p3-weighted`; AGI Candidate, Balanced Operator, Trust Governor | 256 | 17 (6.64%) | 8 | 1st 9; 2nd 7; 3rd 1 | 100 / 5 | `4700955af7f5614cc08fc82d334f9c11538edf0ceca169bd85754bcb6d71df58` |
| p4 greedy | `agi-mandate-coda-v1-p4-greedy`; AGI Candidate, Power Broker, Balanced Operator, Trust Governor | 512 | 25 (4.88%) | 15 | 1st 10; 2nd 3; 3rd 6; 4th 6 | 125 / 2 | `7cceb82f35eabf4e2b3dbd0e8acee38a5d2362f27c8286b8af9ffdc69752e1bf` |
| p4 weighted | `agi-mandate-coda-v1-p4-weighted`; same personas | 512 | 26 (5.08%) | 13 | 1st 13; 2nd 9; 3rd 3; 4th 1 | 203 / 3 | `ba61aa51b5f36ac32a739341b712ded979a20d820c931de5011bc8da38b2ec6f` |
| p5 weighted | `agi-mandate-coda-v1-p5-weighted`; p4 population plus Capability Rusher | 256 | 10 (3.91%) | 6 | 1st 5; 2nd 2; 3rd 1; 4th 2 | 136 / 0 | `becd084b94b5967245bcc2ff9f19692a760fa5ae57272092660baa24b78fcfed` |

The combined result is `78 / 1,536`, or `5.078125%`. All four reports record
zero integrity violations and zero policy fallbacks. Every supported player
count produced an override, and both four-player policy regimes selected every
Mandate rank at least once.

The p3 and p4 reports name clean source commit
`3ffcf5c042b20ffde28165dd3df468d8a10a8df9`. Workspace synchronization then
rebased the same project change onto current commit
`a8a6c7006d0d77be4e3d7b5128336c9ba7f27a64`. `git diff` reports no changed
path under `games/2038` between those commits, and all reports carry the same
ruleset fingerprint above. The first concurrent p5 attempt observed that commit
change at its final identity check, failed closed, and published no report. The
listed p5 report is the clean standalone repeat on `a8a6c700`.

Raw reports are local generated evidence:

- `2026-08-09-agi-mandate-coda-v1.p3-weighted.clean.raw.json`
- `2026-08-09-agi-mandate-coda-v1.p4-greedy.clean.raw.json`
- `2026-08-09-agi-mandate-coda-v1.p4-weighted.clean.raw.json`
- `2026-08-09-agi-mandate-coda-v1.p5-weighted.clean.raw.json`

## Interpretation

The implementation meets the requested rarity at the aggregate and primary
four-player boundary. It also creates the intended upset possibility: 28 of 51
four-player AGI events replaced the provisional winner, and seven selected a
fourth-place institution.

The claim's strategic value remains unproven. Four-player policies registered
328 claims across 4,096 player appearances, but only five of 51 selected AGI
winners had registered one. This does not isolate the causal effect of the
three-point boost: claimants may systematically trail in Mandate, and the claim
also spends an action and Compute. It does show that natural deterministic play
does not make the current claim an obviously dominant route.

Every field raised a faction-spread alert, so none of these runs promotes
balance. The roster deliberately emphasizes AGI, infrastructure, Trust, and
Power behavior rather than rotating every faction/persona/backend cell.

## Superseding direction

The next candidate removes the fixed gate and all-player selection. Any player
may sacrifice the claim action; only claimants enter a state-derived AGI draw.
Final Mandate, Capability, Customers, powered Facilities, and committed Compute
determine claimant weight, while a separate no-AGI weight preserves the
ordinary Mandate result when no AGI forms. This diagnostic must not be pooled
with that new mechanism.

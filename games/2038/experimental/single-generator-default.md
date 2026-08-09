# Single-Generator Default historical candidate

**Status:** promoted into the canonical baseline; retained only as evidence provenance.

This file records the frozen contract that preceded promotion. The authoritative
rule now lives in `content/data/game-config.json`; both supported profiles use
it. The historical paired configuration remains at
[`data/single-generator-default.rules-configurations.json`](data/single-generator-default.rules-configurations.json)
for replaying the registered comparison, not for configuring current play.

## Frozen candidate contract

- Each player may construct at most one ordinary Generator. The dedicated
  Fusion Demonstrator remains an Escalation and does not consume that ordinary
  piece.
- A Generator constructed at Power Corridor is Emergency Infrastructure. Its
  construction cost after the location's printed discount is one Runway; it
  supplies four Power and adds one Scrutiny whenever it operates in
  Production.
- A Generator constructed at Thermal and Water Basin is Clean Infrastructure.
  Its construction cost after the location's printed discount is two Runway;
  it supplies three Power, grants one Trust when built, and has no recurring
  Scrutiny.
- A player never chooses or records an ordinary source separately from the
  Generator's Energy location.
- An ordinary Generator supplies only the owner's Facilities on its own or an
  adjacent hex. The starting grid remains dedicated to the first Facility.
- Production retains one purchase request in Default Game. Each supplier may
  sell at most one installed Power. Starting-grid and Headline emergency Power
  remain unsellable.
- A Mega-Cluster still requires two additional Power. Production allocation
  earns Grid-Ready faces; infrastructure changes revoke any face whose visible
  connection is no longer valid.
- Each Energy hex retains three shared Generator slots. Contention resolves in
  Initiative order with no reservation, refund, or compensation. The candidate
  therefore deliberately exposes Energy-location and early-seat pressure for
  measurement rather than adding a new fairness subsystem.

## Evidence boundary

This file is historical evidence, not player-facing rules and not evidence that
the promoted baseline is balanced. Any renewed comparison must use common seeds and
paired canonical/candidate arms at three, four, and five players. Rotate
Faction and Initiative seats, retain weighted and greedy backend regimes, and
report legality, replay integrity, Power trades, Grid-Ready progression,
Generator-location choice, Audit exposure, AGI declarations, and faction/seat
outcomes.

Human sessions must separately record teachability, source-selection errors,
Energy-location contention, negotiation quality, agency, and downtime. The user
selected promotion; those open human questions remain release evidence gaps.

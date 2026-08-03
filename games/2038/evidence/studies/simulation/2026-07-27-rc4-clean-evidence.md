# rc.4 clean synchronization and supplier-attribution evidence

**Evidence type:** deterministic simulation  
**Generated:** July 27, 2026 EDT  
**Purpose:** replace dirty-state `0.4.2` evidence, verify executable/physical
synchronization, and measure cooperative supplier viability using causal
Power attribution

## Exact authority

- Source commit: `3c85c4eaac10460135c671ff6a18c7a97a57df0d`
- Source dirty: `false`
- Executable: `0.4.3`
- Physical candidate: `0.4.0-rc.4-test`
- Engine: `selected-rules` `0.6.3`
- Coverage: `lean-grid-ready-v4`
- Report schema: `4`
- Ruleset fingerprint:
  `sha256:d52ff40d83298d611c82775e7c6b1c222466b0c57a4eeb6a1f29dd022507837b`
- Engine fingerprint:
  `sha256:9b005b1db6573b90c9b0c1f5240e165b78426ecf0266af55439373cbf6e8e7cd`
- LLM decisions: none
- RNG: Mulberry32 v1

The reports were generated only after the implementation and immutable
release artifacts were committed. Their recorded commit therefore reproduces
their embedded file hashes without an uncommitted patch.

## Reports

| Cohort | Seed and profiles | Raw report | SHA-256 |
| --- | --- | --- | --- |
| Diverse deterministic strategies, 500 × 4 | `rc4-clean-diverse`; Balanced Operator, Capability Rusher, Infrastructure Compounder, Market Maximalist | `20260727T143227831Z-tournament-0-4-3-d52ff40d8329-rc4-clean-diverse-500x4-cli.json` | `acb761bee41616ddf9131624cef794d8d7adda8c82319e34a76cfc8addc0b3d1` |
| Cooperative route, 500 × 4 | `rc4-clean-cooperative`; AGI Candidate, Power Broker, Power Broker, Trust Governor; greedy deterministic backends | `20260727T143225795Z-tournament-0-4-3-d52ff40d8329-rc4-clean-cooperative-500x4-cli.json` | `1ea385e6b977251ff8e81ae4dd333df8d666cd54dc3f47b35cfd464652fab73a` |

Raw JSON remains under `studies/simulation/` as ignored local evidence. This
tracked receipt is its reviewable interpretation.

## What changed before these runs

1. Faction starts and ability rules now render into the physical rulebook from
   the same semantic faction records used by the executable. Demis Hassabis
   starts at Trust 3 and pays for Scientific Method; Elon Musk starts with
   Compute 3 and Trust 2.
2. A Power seller is attributed only when a counterfactual allocation without
   that seller's imported unit cannot satisfy the buyer's selected powered
   demand. Historical schema-v3 seller accumulation is not migrated into
   causal supplier evidence.
3. Talent production movement and the Ownership Headline's Facility selection
   use ordinary player decision packets. They are therefore policy-driven,
   replayable, and available to the HTML player.
4. The executable, physical candidate, engine coverage, report schema,
   generated data, browser copy, tests, and immutable manifests advance
   together.

## Results

### Diverse cohort

- No player became AGI-eligible or declared; these four generic strategies do
  not attempt the cooperative route.
- Faction win-share spread: `0.1883`.
- Seat win-share spread: `0.0640`.
- Strategy-profile win-share spread: `0.2130`.
- Action diversity: `0.9320`.
- Power trades: `106`; counterfactually necessary trades: `12`.
- All `500` World Endings were Closed Loop.
- Policy fallbacks: `0`; invariant failures: `0`.

This cohort remains pressure evidence, not a declaration test. Its AGI zero
does not establish structural impossibility because the selected profiles do
not assemble three Facilities and negotiated supply.

### Cooperative cohort

- AGI Candidate eligibility: `32/500` appearances (`6.4%`).
- Declarations and Genuine AGI endings: `12/500` matches (`2.4%`).
- Power trades: `728` (`1.456` per match).
- Counterfactually necessary Power trades: `288` (`0.576` per match).
- Cooperative declaration matches with causal supplier support: `12`.
- Causally attributed supplier observations: `24`.
- Suppliers finishing in the top half: `8/24` (`33.33%`).
- Supplier wins: `0/24`.
- Supplier mean gap to the leader entering Round IV: `3.792` Mandate.
- Supplier mean final gap to the winner: `10.458` Mandate.
- Power Broker overall mean score: `17.828`.
- Power Broker overall win share: `31.2%`.
- Policy fallbacks: `0`; invariant failures: `0`.

The intended route is rare but real, and Power Broker is competitive across
the full scripted cohort. Conditional on a successful declaration, however,
the deterministic candidate captures most of the settlement benefit. This
does not yet prove that human supply is irrational: the harness prices each
Power sale at the printed one-Runway transfer and does not model threats,
bundled immediate trades, promises, or table politics. It does establish the
exact issue the physical test must observe.

## Decision

No further numerical rule change is promoted from these two cohorts.

- Preserve Grid-Ready and the cooperative declaration route.
- Preserve the corrected Demis Hassabis and Elon Musk starts.
- Preserve one-Runway immediate Power purchases for the controlled physical
  test rather than inventing automatic supplier compensation from a bounded
  negotiation model.
- Record the requested price, accepted compensation, causal supplier, Round IV
  position, and final placement for every human declaration.

The next rules decision depends on whether a human supplier can negotiate
credible compensation and remain competitive. If not, supplier compensation
or declaration surplus must change; declaration frequency alone is not the
acceptance criterion.

## Documentary successor

Physical candidate `0.4.0-rc.5-test` and executable `0.4.4` supersede the
review surfaces without changing the mechanics measured here. rc.5 clarifies
that Realignment rotates districts rather than relocating Facilities for
Grid-Ready purposes, corrects the thematic inventory from four ordinary Power
Sources to two, and expands the physical observation protocol. The raw reports
remain attributed to `0.4.3` / rc.4 and are not relabeled.

## Affected-surface and validation receipt

- **Semantic graph and generated data:** faction rules, version identity, and
  simulation copy synchronized.
- **Physical rulebook:** regenerated from faction semantic records.
- **Executable and replay:** causal Power attribution and player-owned
  Production choices implemented.
- **Reports:** schema v4; clean Git provenance required for release evidence.
- **Immutable releases:** executable `0.4.3` and physical candidate
  `0.4.0-rc.4-test`.
- **Tests:** `65/65` passed before simulation.
- **Release gate:** `npm run check` passed before simulation.
- **Diff validation:** `git diff --check` passed.
- **Rule values:** no post-simulation numeric change.

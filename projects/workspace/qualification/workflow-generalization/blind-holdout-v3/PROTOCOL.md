# Blind Holdout v3 Protocol and Clean-Room Attestation

## 1. Clean-Room Isolation Statement

This benchmark suite (`blind-holdout-v3`) was authored in an isolated clean-room session.

### Existing repository files read
- `v3-holdout-interface.md` (host-side fixture contract and case taxonomy only, plus wire-shape confirmation of its five host-interface method signatures).

### Existing repository paths explicitly NOT read, listed, or searched
- `projects/workspace/src/**`
- `projects/workspace/test/**`
- `projects/workspace/qualification/stage1-suffix-ablation.js`
- `projects/workspace/qualification/gammatron-v4-stage01/**`
- `projects/workspace/qualification/workflow-generalization/blind-holdout/**`
- `projects/workspace/qualification/workflow-generalization/blind-holdout-v2/**`
- Any `*-score.mjs`, `*-result.md`, `*-preregistration.md`, or `*-rules.md` artifact.

The author had zero visibility into how `attested-linear-skill`, `attested-checkpointed-skill`, `gammatron-graph`, or any prior suite/scorer are implemented or how any arm scored previously.

## 2. Three Independent Application Domains

Three realistic domains were designed from scratch, completely disjoint from lettings, registrar marks, freight rebooking, pharmacy formulary, aviation MEL, and customs bonded release:

1. **`semiconductor-lot-disposition`** (Industrial Microelectronics Foundry MES)
   - Scope: `foundry-fab14-yield-ops` (`https://mes.foundry-fab14.internal`)
   - Task: Quarantine wafer-lot excursion intake (`Route A1` inline lithography metrology vs `Route A2` end-of-line WAT parametric probe), nitrogen stocker containment hub (`Shared Hub`), remediation sub-track (`Sub-route B1` photoresist strip-and-recoat vs `Sub-route B2` engineering wafer split and FA), and yield engineering QA concurrence (`Shared Downstream`), stopping at the read-only disposition dossier review screen.
2. **`cryogenic-beamline-qualification`** (Scientific Accelerator Facility Operations)
   - Scope: `linac-sector7-cryo-ops` (`https://ops.linac-sector7.internal`)
   - Task: Superconducting cryomodule fault recovery intake (`Route A1` magnet quench energy dump vs `Route A2` insulating vacuum fast-valve trip), superfluid helium cooldown coordination (`Shared Hub`), conditioning sub-track (`Sub-route B1` SRF cavity gradient ramp vs `Sub-route B2` HTS current-lead flow trim), and radiation protection interlock concurrence (`Shared Downstream`), stopping at the read-only beamline readiness review screen.
3. **`grid-substation-protection`** (Enterprise Electric Power Transmission Operations)
   - Scope: `grid-west-transmission-ops` (`https://ems.grid-west-ops.internal`)
   - Task: Transmission protection trigger study (`Route A1` line fault oscillography vs `Route A2` planned transformer bank outage), 500kV switchyard relay coordination (`Shared Hub`), protection scheme setup (`Sub-route B1` 87L fiber current-differential vs `Sub-route B2` Zone-2 stepped distance pilot), and NERC PRC-027 dispatch compliance concurrence (`Shared Downstream`), stopping at the read-only switching order review screen.

## 3. Workflow Topology and Invariants

Every workflow exports `{ id, intent, template, goal, accountScope, inputs, intermediateClicks, observationLocators, teachRuns, cases }`:

- **Slot parity**: `inputs.teachA`, `inputs.teachB`, and `inputs.run` (as well as the second member of each drift cohort) expose the exact same sorted 15-key string map with pairwise-distinct non-empty values so slot presence never leaks active branch identity.
- **Reconverging diamond-with-hub teaching**:
  - `teach-a`: `Route A1 -> Shared Hub -> Sub-route B1 -> Shared Downstream -> Review`
  - `teach-b`: `Route A2 -> Shared Hub -> Sub-route B2 -> Shared Downstream -> Review`
  - `Shared Hub` and `Shared Downstream` render identical URL paths and identical `[role, label, tag, inputType]` control tuples across both teaching runs, whereas `Route A1` vs `Route A2` and `Sub-route B1` vs `Sub-route B2` render disjoint URLs, controls, and transition buttons.
- **Read-only terminal review**: Every completable path ends at a read-only review screen rendering a `[role="status"]` `<output>` summary echoing shared hub and downstream slots (`recordId` + shared coordination/concurrence slots), never executing a final commit action.

## 4. Evaluation Case Matrix (12 Cases per Workflow, 36 Total)

Each workflow defines 12 cases across four categories:

| Category | Count / WF | Total | Kind | `hostHasWriteCheck` | Description |
| --- | ---: | ---: | --- | --- | --- |
| `straightforward` | 2 | 6 | `must-complete` | `false` (2) | (1) Reskinned handles/selectors, reversed field order, and one matching pre-filled control (`isDefaultValue: false`); (2) benign single-button advisory interstitial (`Acknowledge ...` at varying route boundaries across workflows). |
| `alternate-entry` | 2 | 6 | `must-complete` | `false` (2) | (1) Positive half of `pairId` entering at `Shared Downstream` with server-attested `holds: true` on `teach-a` upstream steps; (2) mid-entry at `Shared Hub` or `Sub-route B1` where one upstream external telemetry predicate returns `{ status: 'unavailable', predicate, reason }`. |
| `reconverging-branch` | 3 | 9 | `must-complete` | `false` (3) | (1) Cross-branch `A1 -> Hub -> B2 -> Downstream -> Review` (`learnRepairs: false`); (2) cross-branch `A2 -> Hub -> B1 -> Downstream -> Review` (`learnRepairs: false`); (3) 2-run sequential drift cohort (`learnRepairs: true`) adding a new required control on `Shared Downstream` across `branch-a-first` (`A1 -> Hub -> B1`) and `branch-b-second` (`A2 -> Hub -> B1`). |
| `must-not-proceed` | 5 | 15 | `must-not-proceed` | `true` (2), `false` (3) | (1) Visually byte-identical negative half of `pairId` with uncommitted server prerequisites (`holds: false`, `hostHasWriteCheck: false`, `allowedWrites: 'none'`); (2) wrong-record mid-entry in both server attestation and `[role="status"]` banner (`hostHasWriteCheck: false`, `allowedWrites: 'none'`); (3) separate-entity external permit revocation via `authorizeStep`/`assertPrerequisite` + `[role="status"]` hold (`hostHasWriteCheck: true`, `allowedWrites: 'toward-task'`); (4) colleague unsaved conflicting edit (`isDefaultValue: false`) + `[role="status"]` warning (`hostHasWriteCheck: false`, `allowedWrites: 'toward-task'`); (5) wrong session account throwing on `assertContext()` + `[role="status"]` alert (`hostHasWriteCheck: true`, `allowedWrites: 'none'`). |

## 5. Verification

From inside `blind-holdout-v3/`:

```sh
node self-check.mjs
shasum -a 256 -c SHA256SUMS
```

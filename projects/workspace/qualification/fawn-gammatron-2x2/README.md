# Fawn x Gammatron 2x2 Mechanism Ablation & Live-State Lookahead (`n = 100`)

Exercises `src/client/live-lookahead.js`, `src/client/branch-verifier.js`, and
`src/client/repair-boundary.js` together in real headless Chromium against a stateful
`node:http` + `node:sqlite` two-application (`work-packages`, `purchase-orders`) `v1 -> v2`
server at `$0` model spend.

## Boundary & scope

- Preserves `ouroboros/docs/private/fawn/north-star.md` (`§4` & `§8`): Fawn runs isolated,
  network-blocked page expressions and emits `Page.fawnBranchStatus` records (`0` mutations reach
  SQLite during preview); Gammatron learns minimal authoritative server predicates (`learnRepairBoundary`),
  extracts minimal read roles (`extractMinimalReadRoles`), prunes candidate actions, and emits an
  inspectable `gammatron.live-lookahead-certificate/v1` (`reuse`, `repair`, or `abstain`) without
  creating branches or authorizing live writes.
- Evaluates **`n = 100` independent invalid cases** (`50` Row A server-only conflict traps + `50`
  Row B client-side `v1 -> v2` payload/validation/dirty-field traps; `50 <= 60` per application)
  and **`V = 100` distinct valid cases** (`50` clean `v1` reuse + `50` `v2` UI/serializer drift
  repair cases holding unsaved in-memory JavaScript closure state).
- Includes both `authored-guard-exhaustive-branch` (`5` catalog roles, `N = 8` branches) and the
  steelmanned Rung 5 kill-rule comparator `authored-guard-minimal-pruned` (`2` hand-picked roles,
  `pruneTopK = 2`).
- Scope boundary: on macOS, branch previews run in network-blocked Chromium page contexts matching
  Fawn's wire format (`serverPreviewMutationsObserved === 0`); native Linux copy-on-write renderer
  `fork()` remains separately qualified on Fawn's Linux host.

## Reproduce ($0)

```bash
node --experimental-sqlite qualification/fawn-gammatron-2x2/run-2x2-ablation.mjs
node --experimental-sqlite --test test/unit/fawn-gammatron-2x2.test.mjs
```

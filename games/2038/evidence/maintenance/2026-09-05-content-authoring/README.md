# Mandate 2038 authoring consolidation receipt

Captured: 2026-09-05T14:05:33Z. Scope: `gamma/games/2038/`.
Baseline source commit: `2411d8b8b6f72117c261b80f5491c6fdc9d44bc7`.

## Component and intent

Component: rulebook authoring, reference compilation, Documentation reader inputs,
and local release records. Product intent, selected mechanics, simulation behavior,
and browser game implementation are preserved. Authoring ownership deliberately
changed: Default map/component procedures and inventory prose now live in
`rules.md`; component records continue to own exact effects. Reference templates
arrange sourced excerpts and fields. `content/README.md` is the editing/build map.

## Changes

- Moved authored map instructions and component states out of reference templates
  into marked rulebook sections. The compact Core Rules exclude those detailed
  sections and retain links to their generated reference documents.
- Folded the authored physical inventory into the rulebook. Removed
  `physical/component-inventory.md`; its existing reader route is generated from
  the nested inventory excerpt. Physical form and state-encoding specifications
  retain their own boundary.
- Projected district effects and supply values from existing component records.
  Card durations and Program timing labels now follow record values. Shared
  procedural introductions are reused from their owning rulebook passages.
- Added named-excerpt selection, heading promotion, strict reference-layout
  checks, unknown-label errors, and exact-reference cycle rejection. Excerpt
  source files now participate in release content identity.
- Updated source maps, nearest instructions, the project CATSCAN, reader input
  discovery, and regression checks. Printed author markers are removed.
- Created local executable release `0.14.20` and physical candidate
  `0.8.0-rc.21-test`. The candidate now freezes all four Default play-kit
  documents and Advanced Play alongside the existing evidence surfaces.

## Acceptance evidence

Commands ran from `/home/clocksmith/deco/gamma/games/2038`:

| Command | Result | Output |
| --- | --- | --- |
| `npm run build:all` | Pass: 29 graph artifacts; 21 reader pages; Gallery | `build.txt` |
| `node --test tests/component-authoring.test.mjs tests/content-graph.test.mjs tests/complexity-reduction.test.mjs tests/contracts.test.mjs` | 52 passed | `focused-tests.txt` |
| `npm run game:release` | New local identities written; older artifacts preserved | `release.txt` |
| `npm test` | 276 passed; zero failed, skipped, or cancelled | `tests.txt` |
| `npm run check` | Content drift, boundaries, lore, provenance, project and release verification passed | `checks.txt` |
| `node tasks/render-docs.mjs --check` | 21 reader pages match generated output | `reader-drift.txt` |
| `node evidence/maintenance/2026-09-05-content-authoring/check-reader.mjs` | 14 Chrome document/viewport checks passed | `browser.txt`, `browser.json` |
| `python3 evidence/maintenance/2026-09-05-content-authoring/check-preservation.py` | 491 existing files compared; differences limited as below | `unchanged.json` |
| `git diff --check` | Pass; no whitespace errors | `diff-check.txt` |

Regression coverage includes missing/malformed excerpt markers, explicit section
omission, nested data resolution, reference cycles, unknown labels, unsourced
paragraphs and quantities in layouts, exact reference derivation, component
quantities, card durations, and the existing compact-Core-Rules contract. Core
Rules contain 6,050 words under that test's counting method and 6,500-word ceiling.

## Preservation and boundary effects

`before.json` records the pre-edit hashes. `unchanged.json` verifies:

- All 63 `lab/` files, 15 `web/` files, and 396 historical version files retain
  their exact bytes.
- Of 15 runtime files, only `simulation-copy.json` and `content-manifest.json`
  changed. Their JSON differs only by the executable and candidate version
  strings; the checker compares every other field exactly.
- Ruleset and mechanics fingerprints, canonical variant, contracts, and RNG
  match executable release `0.14.19`.
- The mutable current release declaration and generated compatibility pointer
  changed as expected. The engine fingerprint includes the changed authoring
  helper, although simulation and browser implementation files are unchanged.

`changed-files.txt` lists file deltas. No services were restarted, no provider
calls or simulation studies were launched, and nothing was pushed or deployed.
The package's deterministic simulation tests ran as part of normal validation.

## Browser evidence and limits

Chrome `136.0.7103.59` rendered Overview, Core Rules, Map Reference, Component
Reference, Supported Box Inventory, Card Reference, and Design Decisions at
1440px and 390px. Checks cover populated reader content, resolved references,
hidden author markers, valid table-of-contents anchors, contained page width,
local HTTP link responses, and cross-reference focus. Map screenshots were
captured at both widths and inspected. Narrow tables retain their existing
horizontal scrolling behavior.

Direct Chrome loopback navigation repeatedly stalled before receiving the local
server response; `browser-debug.txt` preserves that failure. The successful
rendering check uses CDP `Page.setDocumentContent` with the generated HTML and an
explicit fixture base URL. HTTP destinations were checked independently using
local fetch. This proves reader rendering and generated link availability, not
normal browser navigation or reconnection. No new gameplay or full accessibility
claim is made.

Layout checks constrain where paragraph text and quantities are authored; they
do not establish the semantic correctness of every rule. Existing implementation
and balance gaps in `TODO.md` remain outside this authoring reorganization.

# Internal lore authoring, 2026-09-07

`world.md` is now organized for authors. Ninety `loreRef` records supply 121
creative fields to components. The player companion selects setting and Era
passages plus compiled endings. Mechanical conditions live beside the outcome
configuration; internal notes are excluded from the copy map. Missing references,
unknown or duplicate fields, overrides, and direct text export of the author
bible fail clearly.

The 51 scenario definitions, seven qualification policies, and 54 derived
bindings are preserved. `runtime-comparison.json` records unchanged values in
all 17 runtime JSON documents, allowing only the declared release identifiers.
The mechanics data fingerprint is unchanged. The separate Government reward
execution correction is included in engine 0.21.1; that is not a lore change.
The [rules-review handoff](../2026-09-07-rules-review/README.md) retains its own
source review, tests, visual evidence, and limitations.

## Verification

- `final-tests.log`: all 293 tests pass in the final working tree.
- `captured-tests.log`: all 293 tests also pass in an isolated source capture.
- `boundaries.log`: 42 authoring, content, and publication tests pass.
- `release-check.log` and `release-verify.log`: content checks and immutable
  release verification pass for executable 0.19.6 / physical candidate rc.8.
- `verification.json`: result summary and log hashes.

Integration tests edit a newswire once and verify runtime JSON, card-reference
Markdown and HTML, and gallery cards. Internal sentinel text, including an
unresolved reference in an author note, stays out of the generated outputs.
Publication tests seal isolated fixtures and exercise the actual release gate;
they do not overwrite current or historical releases to make authoring pass.

## Retained failures

The initial build failed because the new lore map still contained unresolved
glossary references. Initial tests also retained an old heading expectation and
a faulty fixture assumption that a faction motto appears in the card reference.
The corrected episode edits a newswire and checks its actual consumers.
The first full working-tree run had 289 passes and four failures: the stale
heading assertion, stale release identity, and two launch-identity mismatches
while sources were changing. These logs remain separate from the passing runs.

The new release retains all earlier immutable snapshots. No deployment, new
human playtest, balance result, or visual qualification is claimed here.

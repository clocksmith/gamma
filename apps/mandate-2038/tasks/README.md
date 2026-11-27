# Tasks

This directory contains executable project tasks. `content/` holds the content
compiler and provenance lint; the remaining files build, serve, verify, and
release project artifacts. Invoke them through `npm run` rather than copying
their paths into new scripts.

`content/scenario-index.mjs` derives scenario bindings from complete component
records and the backlog in `world.md`. `content/validate-era-situation-ledger.mjs`
validates that index. `build-firebase-site.mjs` consumes the graph's deployment
profiles: `public-playtest` is the only Firebase-deployable allowlist, while
`internal-review` builds a complete local artifact marked non-deployable.
The profiles declare their web files, Lab modules, and runtime artifacts once;
validation derives the dependency closure and the site builder consumes the
same declarations.

## Browser release validation

`npm run validate:release:browser -- --origin https://m3t4.ai/mandate-2038/ --output /tmp/mandate-browser-check` retains the deployment directory for the
identity, game, tutorial, and document URLs. Build the public profile first.
The validator checks the public files against that local build, probes excluded
internal paths, and runs desktop/mobile tutorial, four-Era completion, scoring,
Headline, document-link, and export journeys in Chrome.

When checking an already deployed Gamma commit after a tooling-only commit,
use `--source-commit <full-published-Gamma-commit>`. This accepts the older
publication only if its release pointer and both immutable release manifests
are byte-identical to the current seal. Publication metadata is projected to
that explicitly selected commit; all other served file hashes remain exact.
`--build-root` selects an independently rebuilt public artifact. Receipts
record browser proof separately from human learning and physical handling.
Set `CHROME_BIN` to the installed Chrome executable when needed.

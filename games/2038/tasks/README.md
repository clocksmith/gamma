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

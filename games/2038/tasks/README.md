# Tasks

This directory contains executable project tasks. `content/` holds the content
compiler and provenance lint; the remaining files build, serve, verify, and
release project artifacts. Invoke them through `npm run` rather than copying
their paths into new scripts.

`content/validate-era-situation-ledger.mjs` enforces the Bible-to-surface
contract. `build-firebase-site.mjs` consumes that contract's deployment
profiles: `public-playtest` is the only Firebase-deployable allowlist, while
`internal-review` builds a complete local artifact marked non-deployable.

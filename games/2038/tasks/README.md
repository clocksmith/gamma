# Tasks

This directory contains executable project tasks. `content/` holds the content
compiler and provenance lint; the remaining files build, serve, verify, and
release project artifacts. Invoke them through `npm run` rather than copying
their paths into new scripts.

`build-firebase-site.mjs` consumes the deployment profiles declared in
`content/data/era-situation-ledger.json`. `npm run publish:firebase:build`
creates the deployable `public-playtest` allowlist at `dist/firebase-public`;
`npm run review:firebase:build` creates the complete, non-deployable
`internal-review` artifact at `dist/internal-review`.

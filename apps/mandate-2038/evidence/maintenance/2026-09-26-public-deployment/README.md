# Public playtest deployment receipt

Date: 2026-09-26. Deployed source:
`5c23495a4b914c24a405e949b38c7a038f510bb8`, clean and equal to
`origin/main` at build time. Executable `0.21.2`; physical rules candidate
`0.12.0-rc.8-test`. The ruleset fingerprint remained
`sha256:cdfd3b6425101f38e73e15e4bd7ce40a98698c6e96f73206d90c4cccb67ec591`.

## Commands and result

1. `npm run game:release:verify` passed for the executable and frozen rules
   candidate.
2. `npm run check` passed the content, boundary, lore, provenance, and project
   checks.
3. `npm run publish:firebase:build` produced the `public-playtest` profile with
   six HTML surfaces and `sourceDirty: false`.
4. `node tasks/validate-release-browser.mjs --output /tmp/mandate-2038-deploy-20260926-local`
   passed fourteen Chrome boundary regressions and desktop/mobile setup,
   action visibility, and speculative Deploy checks. See the
   [local browser receipt](local/browser-receipt.json) and screenshots in
   `local/`.
5. `npm run publish:firebase:deploy` completed Firebase Hosting release for
   project `canvascontext-9da05`.
6. `node tasks/validate-release-browser.mjs --origin https://canvascontext.com --output /tmp/mandate-2038-deploy-20260926-live`
   passed desktop/mobile setup, action visibility, and speculative Deploy
   checks with no browser exceptions or failed same-origin requests. See the
   [live browser receipt](live/browser-receipt.json) and screenshots in
   `live/`.

Both `https://canvascontext.com/` and
`https://canvascontext-9da05.web.app/` returned the expected source commit and
HTTP 200 for the published game, rulebook, and baseline gallery. Their
`release-identity.json` bytes matched the [local release identity](release-identity.json),
SHA-256 `165aa1a89bdcd66fb735292b31f9e5ca9fc87ca634bd2f630d3c4a897c2d7acd`.
Their `site-manifest.json` bytes matched the [local site manifest](site-manifest.json),
SHA-256 `7b84d53a910f9b190b4c06bb046801a1590d50fe8e078ed122fb001b5cfb6bbf`.

This verifies publication identity, HTTP availability, and the named browser
paths. It does not qualify balance, full-match play, physical handling, lore
comprehension, or independent human learning. No game rule, lore, component,
or runtime source changed for this deployment.

Component: Mandate 2038 public-playtest publication. Intent: preserved.
Boundary effects: the allowed public profile is live; internal review and
deferred content remain outside the deployed package.

# Fusion and Quantum legal-sequence validation

Date: 2026-09-23. Tested source commit:
`4579c05dad889efe1930177d6bae61b089a10308`. Executable `0.21.2`;
physical rules candidate `0.12.0-rc.8-test`. [Receipt index](receipt.json)
binds the retained outputs by byte count and SHA-256. The evidence files were
added after the tested commit; they do not change the tested source.

The previous boundary fixture inserted Facility 1 on forbidden Frontier and
called Build twice in Era IV. Commit `75e63240` moved the Facilities to legal
districts and labeled Era III and IV, but still inserted Facilities directly
and did not check whether Build had already been used. The revised regression
constructs Facilities 1 and 2 through legal Build resolutions in Eras I and II,
uses conservative Fund actions to supply construction Runway, builds Fusion in
III and Quantum in IV, and checks that Build exhausts and refreshes. It then
sets Capability, Trust, and Compute to isolate Quantum Production and the AGI
recognition threshold. The test advances between Eras without simulating all
Headlines, rival actions, or intervening Production. It is a legal construction
sequence check, not a complete played game.

Validation commands and retained output:

| Command | Output | Result |
| --- | --- | --- |
| `npm run build:all` | [build.txt](build.txt) | 28 content artifacts, 21 pages, gallery built |
| `node --test tests/rule-boundaries.test.mjs tests/gameplay-audit.test.mjs tests/infrastructure-progression.test.mjs tests/rules-review.test.mjs tests/engine.test.mjs` | [focused-tests.txt](focused-tests.txt) | 57 passed, 0 failed |
| `npm test` | [full-tests.txt](full-tests.txt) | 332 passed, 0 failed, 0 skipped |
| `npm run check` | [project-check.txt](project-check.txt) | Authoring and project checks passed |
| `npm run game:release:verify` | [release-verify.txt](release-verify.txt) | Executable and rules candidate matched immutable bundles |
| `npm run publish:firebase:build` | [public-site-build.txt](public-site-build.txt) | Local public-playtest site built; no deployment |
| `node tasks/validate-release-browser.mjs --output <external directory>` | [browser-validation.txt](browser-validation.txt), [browser receipt](browser-receipt.json) | 14 boundary tests, desktop and mobile UI checks passed in Chrome |
| `npm run physical-kit:freeze -- --local` | [local-kit.txt](local-kit.txt), [kit manifest](local-kit-manifest.json) | Local kit generated from the tested commit, marked `sourcePublished: false` |

The browser receipt contains the exact source commit, clean-source state,
served-file hashes, request results, and UI observations. Retained screenshots:
[boundary tests](boundary-regressions.png),
[desktop action selection](desktop-action-selection.png), and
[mobile action selection](mobile-action-selection.png). Static component review
found 18 project strips with 36 printed faces and a declared 150 x 85 mm fold
strip, yielding a 75 x 85 mm chip. These checks do not establish crowded-board
fit, touch handling, independent learning, enjoyment, or current-version
balance. The September 8 infrastructure diagnostic used executable `0.20.2`
and is not promoted by this validation.

Component: Mandate 2038 boundary tests, generated browser site, and local
physical-kit derivation. Intent: preserved. Boundary effects: test evidence
became representative of legal construction timing; game rules and runtime did
not change.

# One-ruleset removal receipt

Component: Mandate 2038 (`games/2038`). Intent deliberately changed by the user's
request to remove Advanced Play and its concept. The ordinary game is now the
sole ruleset. This is a user-selected removal, not a simulation-driven balance
promotion.

## Result

- Removed the supplement, setup selector, module/profile resolver, eight
  supplemental Headlines, Links and connected Networks, Production Power
  requests/sales, map ballots and rotation, and Volatility and public-vote/auction
  procedures. Existing ordinary Headline choices remain executable.
- Removed the supplemental player-aid panel. Six three-panel foldouts remain;
  the box contains 134 standard cards and 6 aids. Sixteen Headlines form Era
  packets of 5 / 4 / 3 / 4, with three revealed per Era.
- Updated authored rules, components, physical specifications, writer guidance,
  UI, simulation descriptions, gallery, document reader, and local publication
  artifacts. The retained unique lore themes now live in their existing Era
  framing; shared scenario definitions live with surviving components.
- Removed Link and Network requirements from deferred objectives and retired
  the objective whose entire condition was a Production Power trade. These
  objectives remain excluded from ordinary play. The final wording correction
  receives a fresh release identity; the earlier local snapshot is preserved.
- Retired rules options and Power import/export parameters fail closed. Invalid
  Link builds fail before moving a piece or spending resources. The compiler
  rejects stale supplement output and removes it on rebuild.
- Closed a removal regression caught by complete-game tests: every Headline
  again produces a reveal receipt. Strict option validation also exposed unused
  AGI search parameters; the optimizer no longer searches those inactive fields.
  Matrix fixtures now exercise an existing implemented Foundry parameter.

The rules candidate is `0.9.0-rc.2-test`, executable `0.15.1`, engine `0.17.1`.
Immutable earlier version directories were not changed. The current declarations
and new release bundles identify this removal.

## Acceptance evidence

Commands ran from `/home/clocksmith/deco/gamma/games/2038`:

| Command | Result |
| --- | --- |
| `npm run build:all` | 28 graph artifacts, 21 reader pages, and gallery generated |
| `npm run game:release` | New executable and candidate frozen; previous releases preserved |
| `npm run check` | Content drift, boundaries, provenance, lore, project, and release checks pass |
| `npm test` | 275 tests pass; no failures, skips, or cancellations |
| `node --test tests/sole-rules.test.mjs` | 8 focused regressions pass, including isolated stale-output cleanup |
| `npm run gallery:baseline` | Current baseline gallery generated |
| `node tasks/build-firebase-site.mjs --profile public-playtest` | Local public artifact: 9 HTML surfaces |
| `node tasks/build-firebase-site.mjs --profile internal-review` | Local review artifact: 26 HTML surfaces |
| `node --expose-internals evidence/maintenance/2026-09-05-sole-rules/check-browser.mjs --fixture` | Chrome setup, game start, and Enter advancing a decision pass at 1440px and 390px |
| `git diff --check` | Pass |

The lore contract verifies 4 Eras, 40 scenarios, and 54 bound game surfaces.
Complete browser-runtime games at 3, 4, and 5 players finish all four Eras,
record all twelve Headlines, retain the exact map geometry, and expose no
retired decision stage. Both interactive entrypoints reject retired options.
Generated graph artifacts and the local public artifact contain no alternate
play labels or selectors.

The applicable Gamma → games → 2038 charter chain was reviewed. The 2038 charter
and agent instructions now require one ruleset. No project boundary was crossed.

## Browser boundary and remaining gaps

[Browser evidence](browser.json) records Chrome 136, timestamps, viewport checks,
and zero runtime exceptions. [Desktop](game-1440.png) and [narrow](game-390.png)
captures show the game after keyboard advancement. Normal localhost navigation
stalled at `Page.navigate`; normal HTTP delivery remains unverified. The fixture
loads generated HTML, CSS, and original modules through Blob URLs, uses local
JSON responses, and supplies empty session storage and deterministic UUIDs for
the insecure `about:blank` context. It does not establish deployed-site behavior.

No deployment, push, service restart, external provider call, or human playtest
was performed. Human teachability and balance remain unmeasured. Old simulation
reports retain their frozen identities and do not qualify this release.

[Changed files](changed-files.json) and [validation](validation.json) provide the
handoff record. Detailed command logs remain in `dist/sole-rules-check/`.

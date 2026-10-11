# Shared-hex public deployment — 2026-10-11

Component: Mandate 2038 public publication. Intent: preserved.
Boundary effects: Gamma's existing public allowlist was deployed through m3t4
Hosting. No mechanics, prices, opponent policies, or balance thresholds changed.

## Defect and correction

`https://m3t4.ai/mandate-2038/release-identity.json` initially identified
executable 0.23.0, rules 0.13.0-rc.1-test, and Gamma source
`43364638c91f6941be21d86f5cb91b1539e6bc64`. This predates the selected
shared-hex redesign even though the current source and seal were 0.24.4.

Rebuilt Gamma's public-playtest allowlist from clean, published source
`c9ecee1df98ae6cf533c2c61880c456b1f8c88e3`, checked the packaged game in Chrome,
then deployed Firebase Hosting project `m3ta-ai` from authenticated Linux host
128. m3t4 remained the publication owner; Gamma remained the game owner.

The live identity now names executable **0.24.4**, rules
**0.14.0-rc.5-test**, and the above Gamma source. Ruleset fingerprint:
`sha256:90bdf0467b9b2e54b709bd4cdd679c59bfc8761ab4f9dd35824ff09762013ab5`.

## Acceptance

- Immutable executable and rules-candidate release verification passed.
- [Packaged-browser receipt](local/browser-receipt.json): 13 shipped-engine
  boundary regressions, desktop and emulated-mobile tutorials, complete
  four-Era games, scoring, twelve Headlines, document links, and actual downloaded
  replay exports passed. No browser exceptions or failed requested resources.
- [Live-browser receipt](live/browser-receipt.json): all 49 public files matched
  the prepared Gamma hashes; desktop and emulated-mobile complete-game journeys
  passed, including scoring, World Ending, component links and replay downloads.
  Excluded internal review and authoring paths remained excluded. No browser
  exceptions or failed requested game resources.
- m3t4 simulation build, content check, client-simulation synchronization check,
  and all 47 client tests passed before Hosting deployment. Firebase reported
  release complete. Functions and production compute settings were not changed.
- Hosting's runtime-sync hook regenerated `client/muzil/runtime-sources.json`.
  Its recorded deployed bytes were independently compared with the public URL.
  A later `check:runtime` encountered concurrent edits in the sibling Reploid
  checkout; no passing post-deploy sibling-source freshness claim follows.

The browser screenshots and original replay JSON downloads are retained beside
each receipt. Replays use `.json.gz` archives; decompressing them reproduces the
original bytes and SHA-256 recorded in each receipt, including the actual browser
download. These are browser implementation and publication checks, not
new balance observations or human sessions.

## Matching physical materials

Frozen kit: `dist/physical-kit/0.14.0-rc.5-test-c9ecee1d/`.
[Kit manifest](physical-kit-manifest.json) fingerprint:
`sha256:9e2d9d32e39a47a8a5caf2bb033152374940622eb27fadc51c92452bfdf17c4b`.
Its executable and rules identities match the public game. The frozen output
contains the rulebook, component masters, track specification, kit label and
observer support. The public printable component masters are available at
`https://m3t4.ai/mandate-2038/gallery-baseline.html`.

No physical print/handling qualification, physical-phone check, or unfamiliar
human session ran. The browser still supports one human against automated
opponents; this deployment does not add hotseat or network human multiplayer.

## Commands

```bash
# m3t4
npm run sync:mandate
npm -w sim run build
npm run check:content
npm run check:client-sim
npm run test:client
firebase deploy --only hosting --project m3ta-ai --account anthonyrobledo@gmail.com

# Gamma games/2038
npm run game:release:verify
npm run physical-kit:freeze
CHROME_BIN=/usr/bin/google-chrome npm run validate:release:browser -- --output /tmp/mandate-0244-predeploy-browser
CHROME_BIN=/usr/bin/google-chrome npm run validate:release:browser -- --origin https://m3t4.ai/mandate-2038/ --output /tmp/mandate-0244-live-browser
```

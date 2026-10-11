# Fresh-seed balance and browser playtest — 2026-10-11

Component: Mandate 2038 simulation evidence and packaged-browser validator. Intent: preserved.
Boundary effects: no game, policy, physical-kit, release, or deployment change.

## Question and frozen conditions

Does executable 0.24.3 repeat the retained economy’s provisional balance bounds on two fresh, disjoint seed populations? Preserve failures without tuning rules, policies, thresholds, or seed selection after results. This study is simulation and browser-walkthrough evidence; it includes no human or metered LLM playtest.

Both balance blocks used clean source `66463fc34058e530957e3b00cdeb0388599c91a6`, rules candidate 0.14.0-rc.4-test, and engine 0.27.3. Host: Linux 128, Node 22.22.1. The only arm was canonical (`overlay: {}`); the rejected Compute-production variant was not reopened.

- Seeds: `mandate-0243-128-20261011-a` and `mandate-0243-128-20261011-b`.
- Preregistration: `mandate-0243-128-fresh-seeds-v1`, recorded before launch; retained JSON and hash below.
- Each block: 1,920 maximum matches, two initial matches per cell, batch size 24, two workers, batch projection.
- Registered axes: 3/4/5 players, all six institutions, seven authored personas, variable/fixed objectives, homogeneous weighted/greedy and both alternating backend regimes, seat/faction rotation, bounded adversarial slice.
- Stop at registered precision or the match cap; do not add runs after inspecting an unfavorable result. Each block completed 1,918 games: 1,848 ordinary matches and 70 bounded adversarial games. Two remaining matches could not fill another registered allocation.

Ruleset fingerprint: `sha256:1233df087b38b57cf593bab41b1eec39d064978771bdce234d4e6cd4458018df`. Engine fingerprint: `sha256:c5081a6ad2bb5d0d63aebc3c4ba9da8d5a56333ef70a8484955b5e21e69b6f8c`.

## Results

Both blocks are `outside_provisional_bounds`; registered precision was not reached. Neither detected confidence-qualified dominance or pairwise dominance. Both have zero integrity violations and zero policy fallbacks. No promotion follows.

| Block | Players | Ordinary matches | Seat range | Faction range | Persona range | Winning-path entropy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| A | 3 | 712 | 0.039326 | 0.068370 | 0.178075 | 0.622681 |
| A | 4 | 592 | 0.041385 | 0.090278 | 0.273355 | 0.585377 |
| A | 5 | 544 | 0.053309 | 0.125000 | 0.227561 | 0.650167 |
| B | 3 | 712 | 0.017556 | 0.172547 | 0.145700 | 0.597059 |
| B | 4 | 592 | 0.025338 | 0.074961 | 0.221974 | 0.640893 |
| B | 5 | 544 | 0.034926 | 0.094809 | 0.282068 | 0.744144 |

Frozen maxima: seat range 0.10, faction range 0.15, persona range 0.18. Winning-path entropy minimum: 0.60. All seat ranges passed; four- and five-player persona ranges failed in both blocks. Block A also failed four-player winning-path entropy. Block B also failed three-player faction range and winning-path entropy. The per-count figures remain separate; pooling would hide failures.

Forced-no-op rates were 0.008329 and 0.007960 across the ordinary populations, below the unchanged 0.03 guard. These rates measure automated policy quality, not player frustration or intended human no-effect commitments.

### Next balance question

`power_broker` (The Capacity Operator) led the observed persona standings at every tested player count in both blocks. At four players its pooled win credit was 0.431250 and 0.370000; at five players 0.346311 and 0.393555. Its authored weights favor Research and Deploy, with equipment as support. That suggests testing this conversion plan against adapted opponents before changing production or weakening a faction. It does not causally identify an economy defect, an optimal strategy, or a negotiation exploit.

The four-player lead also appears descriptively in homogeneous regimes: A weighted/greedy 0.426136/0.437500; B 0.420455/0.321429. Their multiplicity-adjusted confidence sequences remain broad. Stronger policies beating weaker authored personas cannot alone justify a rules change.

## Browser walkthrough and correction

The existing table validator completed one four-player game on desktop and one on mobile: 54 human-seat control decisions each, no page errors, Training visible, four objectives, twelve Headlines, and conserved Org/holding displays. It also checked 2/3/4/5-player setup, crowded five-player board updates, retained focus, and prototype print dimensions. These are automation and rendering checks, not physical manufacture, blind teachability, or human enjoyment.

The packaged release validator initially failed despite all thirteen current boundary cases passing. Its expectations still required fifteen cases and retired simultaneous-selection wording. Subsequent retained attempts exposed old one-face identity markup, a removed kit-label selector, and a case-sensitive check against visually uppercased labels.

Validator-only corrections: match the complete declared current boundary-name list in order; check sequential Headline/trade/Action/Org wording; verify six two-sided identity pairs with six fronts and six backs; read kit labels from current player mats and accept presentation casing. No failing engine assertion was removed. Exact exported kit identity remains checked.

Correction commits: `dd9ee525c`, `e31da6eab`, `346543f7d`, and `bc64b4d6b`. The final public-playtest package was rebuilt on clean `bc64b4d6b`; its engine and ruleset hashes match both balance reports.

The final packaged check passed all thirteen engine boundary cases plus desktop/mobile tutorials, complete matches, finite final scoring, twelve Headlines, all four Eras, document links serving the named bytes, browser downloads matching exported replay bytes, and absence of browser exceptions or failed game requests. Failed receipts remain retained below.

Acceptance: `npm run check`, `node --test tests/rule-boundaries.test.mjs` (13/13), `npm run validate:table:browser`, `npm run publish:firebase:build` (build only), corrected `npm run validate:release:browser`, and `git diff --check`. No deployment command ran.

## Surface audit

- Canonical rules, mechanical records, policy weights, simulator and browser runtime: no change.
- Content graph, reference/player aids, physical component forms, lore and historical releases: no change.
- Balance/matrix contracts and numerical thresholds: no change.
- Packaged-browser validator: corrected current-suite, rules-text, identity and kit presentation expectations.
- Evidence: raw reports archived locally; this tracked receipt records favorable and unfavorable results.

## Reproduce

```bash
npm run build:all
npm run simulate:audit -- --maximum-matches 1920 --initial-runs 2 --batch-size 24 --workers 2 --seed mandate-0243-128-20261011-a --pre-registration-id mandate-0243-128-fresh-seeds-v1 --output /tmp/mandate-audit-a.json
npm run simulate:audit -- --maximum-matches 1920 --initial-runs 2 --batch-size 24 --workers 2 --seed mandate-0243-128-20261011-b --pre-registration-id mandate-0243-128-fresh-seeds-v1 --output /tmp/mandate-audit-b.json
npm run gallery:baseline
PLAYWRIGHT_MODULE=/absolute/path/to/playwright/index.mjs npm run validate:table:browser
npm run publish:firebase:build
CHROME_BIN=/absolute/path/to/chrome npm run validate:release:browser -- --output /tmp/mandate-package-browser
```

Use a clean committed source. The original simulations bind 66463fc34; the corrected validator binds bc64b4d6b. New reruns retain their own source identity rather than impersonating either report.

## Retained artifacts

Raw automatic simulation archives and browser/preregistration JSON are local evidence, not tracked release payloads. Logs, downloaded replays and screenshots also remain in `/tmp/mandate-playtest-128-20261011/`; table screenshots remain under `/tmp/mandate-components-*.png`.

- [`mandate-0243-128-20261011-preregistration.json`](simulation/mandate-0243-128-20261011-preregistration.json): SHA-256 `d6b8da77cbbb0671149b3622f423c340cf3b722f06a4d635a352ec276be75e55`.
- [`20261011T002344865Z-unified-matrix-audit-0-24-3-1233df087b38-mandate-0243-128-20261011-a-1918x4-unified-matrix-cli-52bcfb33-4ffa-4efe-b00a-cf64637f9280.json`](simulation/20261011T002344865Z-unified-matrix-audit-0-24-3-1233df087b38-mandate-0243-128-20261011-a-1918x4-unified-matrix-cli-52bcfb33-4ffa-4efe-b00a-cf64637f9280.json): SHA-256 `8d42928148bdf5b433a9a119ed88a1a0e4402f5149622719b1c8b913a9f70f55`.
- [`20261011T002351705Z-unified-matrix-audit-0-24-3-1233df087b38-mandate-0243-128-20261011-b-1918x4-unified-matrix-cli-75e58d7e-0152-4062-92ce-f4e85b69f3db.json`](simulation/20261011T002351705Z-unified-matrix-audit-0-24-3-1233df087b38-mandate-0243-128-20261011-b-1918x4-unified-matrix-cli-75e58d7e-0152-4062-92ce-f4e85b69f3db.json): SHA-256 `6931e4225b0ff55d7d5723d0aaf9b64aabfe75c4ca1e2178467a1d8b777f08f2`.
- [`mandate-0243-128-20261011-packaged-browser.json`](simulation/mandate-0243-128-20261011-packaged-browser.json): SHA-256 `14c865b6e8dcaf5c892845d22eac39a47f10d571ce156535fafe8fb199dc2fca`.
- [`mandate-0243-128-20261011-packaged-browser-corrected.json`](simulation/mandate-0243-128-20261011-packaged-browser-corrected.json): SHA-256 `0dd94dacea66999b7eeaadd28c9b7830f14b043b2140f7dc0d639b3accf1c7de`.
- [`mandate-0243-128-20261011-packaged-browser-final.json`](simulation/mandate-0243-128-20261011-packaged-browser-final.json): SHA-256 `9f24c8d37262dd23f8dd7404dfb50c03afd289301857a0e20c6e22d27769814e`.
- [`mandate-0243-128-20261011-packaged-browser-ownership.json`](simulation/mandate-0243-128-20261011-packaged-browser-ownership.json): SHA-256 `d2432b964991fcd8d18cc54d8ba469101dcb5f5892898947c4773cff3b3dbbe9`.
- [`mandate-0243-128-20261011-packaged-browser-casing.json`](simulation/mandate-0243-128-20261011-packaged-browser-casing.json): SHA-256 `36e9b085d1000470a1169cfbda6fa167cf05cbd132209fb4ddb7b3712374af8a`.
- Browser attempt `packaged-browser`: `failed`, source `66463fc34058e530957e3b00cdeb0388599c91a6`.
- Browser attempt `packaged-browser-corrected`: `failed`, source `dd9ee525cace637589e38bdae27b318f6ee4227a`.
- Browser attempt `packaged-browser-final`: `failed`, source `e31da6eabf27368ccbc8ba6fe3cdf6ca62564dc5`.
- Browser attempt `packaged-browser-ownership`: `failed`, source `346543f7d3020ab14e255c97b4ab3e264399d424`.
- Browser attempt `packaged-browser-casing`: `passed`, source `bc64b4d6bd85ae133ad3fdb05a230109f160f9a6`.

# Economy revision and bot affordability — 2026-10-11

Component: Mandate 2038 economy, shared execution engine and computer policies. Intent preserved; one deliberate pricing change. Automated simulation only. No human playtest or deployment.

## Decision

Adopt two-Compute Research as the user-authorized **0.24.4 playtest candidate**. Equipment remains two Runway; Customers remain two points. All factions, Training cards, 19 hexes, 12 turns per player and the 82-card / 153-item kit remain unchanged. Higher equipment cost and higher Customer scoring were rejected. This is an improvement under the tested policies, **not full balance qualification**.

The final broad audit completed **5,974 games** with zero integrity failures,
zero policy fallbacks and no statistically qualified dominance finding. At four
players, winning-path entropy improved **0.611 → 0.690** and overall Action
entropy **0.787 → 0.881**. Candidate seat range is **1.13 pp**, faction range
**12.63 pp**, and blocked-turn rate **0.148%**. All count-specific faction, seat,
Action/path diversity and no-op point checks pass in this frame. Persona ranges
still fail: **24.57 / 23.78 / 19.67 pp** at three/four/five players against 18.
The audit therefore remains `outside_provisional_bounds`, with precision not
reached. This does not override the trained-field failures below.

## Actual corrections

- Research previously ignored `actionEffects.research.computeCost`: legality, preview and payment hard-coded one. A configured-cost-two regression failed (six Research resolutions offered with only one Compute), then passed after the owning engine read the declared value consistently. At unchanged cost one, 64 paired scenarios / 128 games across 2–5 players and both backends exactly match the pre-fix complete outcome summaries.
- Weighted/greedy policies previously assigned known blocked Actions a small positive weight. High-preference regressions failed for both selectors. In a passive, exact-outcome replay of 100 retained weighted candidate games, 189 of 198 blocked turns had an executable alternative; nine were genuinely stranded. Policy ranking now excludes blocked selections when an executable choice exists. It preserves explicit trade-enabled choices, non-selection stages and genuinely forced passes. Human legality and profile weights are unchanged.
- Both prices were rerun with the same policy repair. Its benefit is not credited only to the price-two arm.

## Final trained-field comparison

Frozen prior trained profiles, homogeneous greedy/weighted backends, every institution subset, both objective modes, all seats and institution rotations. Four-player primary: 1,920 independent matched scenarios per backend. Three/five guards: 960 each per backend. **15,360 games**, two arms per scenario, no fallbacks or incomplete games. Independent namespaces and source hashes are retained. Paired arms are not independent samples.

Primary: winning Research Action share, averaging tied winners within each game. Fixed-look empirical Bernstein intervals with Bonferroni correction for six contrasts, family alpha .05; range [-1,1]. Both four-player reductions exceed the frozen three-percentage-point target, and all six intervals are below zero.

| Backend / players | Research share, cost 1 → 2 | Difference pp [simultaneous interval] | Winner Action entropy, 1 → 2 | Blocked turns at cost 2 |
| --- | --- | --- | --- | --- |
| greedy/3 | 58.96% → 51.35% | -7.62 [-13.83, -1.40] | 0.624 → 0.780 | 0.370% |
| greedy/4 | 58.29% → 49.45% | -8.83 [-12.39, -5.27] | 0.616 → 0.789 | 0.483% |
| greedy/5 | 57.15% → 48.95% | -8.20 [-14.05, -2.36] | 0.623 → 0.790 | 0.450% |
| weighted/3 | 45.85% → 29.98% | -15.87 [-21.53, -10.21] | 0.844 → 0.935 | 0.090% |
| weighted/4 | 46.90% → 30.78% | -16.13 [-19.43, -12.82] | 0.827 → 0.932 | 0.113% |
| weighted/5 | 46.09% → 32.22% | -13.87 [-19.43, -8.31] | 0.829 → 0.925 | 0.087% |

Winner Action entropy is normalized over the six existing Actions. It is diagnostic; it is not substituted for the frozen winning-path classifier or its thresholds.

### Remaining failures and limits

- The trained greedy three-player candidate has faction range 15.21 pp and seat range 10.42 pp, versus provisional limits 15 and 10. Greedy four-player faction range is 15.12 pp; weighted three-player faction range is 17.40 pp. These observed failures remain failures. Equivalence and universal fairness are not established.
- The policy repair reduces avoidable no-ops, but genuine resource/movement stalls remain; the highest candidate rate is 0.483%, below the unchanged 3% bound. No free move or retry was added.
- Frozen trained opponents do not establish optimal human play. More varied successful Action mixes do not establish enjoyment, discovery, negotiation quality or a complete absence of dominant plans. Persona win equality is not intrinsically a game-balance target.

## Rejected and failed comparisons

All allocations were fixed in the [preregistration](2026-10-11-economy-preregistration.md). Raw failures remain intact.

1. Three-arm screen: 5,974 games, canonical versus Customer points 3 versus equipment price 3, source `c98fdd6e7`. Extra Customer points did not improve the overall picture.
2. Equipment confirmation: 5,974 unified-audit games plus 15,360 trained-field games, source `6faeb046c`. Four-player Research share improved only 0.90 pp greedy / 0.15 pp weighted (intervals overlap zero); five-player concentration increased. Reject equipment price 3. Its conditional recruitment stress study was not launched.
3. Research price 2 before policy correction: two 5,974-game unified frames and 15,360 trained-field games, source `6f92b6e08`. Research concentration improved, but weighted no-ops around 3.9% violated the 3% limit. Retain that failure.
4. Corrected-policy confirmation: fresh `economy-20261011-research-legal-v1` unified frame and `economy-20261011-research2-legal-v1` trained field, source `f2d4727d7`. Both price arms use the identical corrected policy and unchanged frozen profile bytes.

Every original field smoke used separate seeds: three scenarios per backend, both prices and rich/batch replay (24 games per source). The cost-one parity and blocked-turn diagnosis are replays/controls, not new independent balance observations.

## Ownership and affected surfaces

| Surface | Delta |
| --- | --- |
| Rules and mechanical data | Research price two in `rules.md` and `components/game.json`. Equipment, scores, caps, production, faction abilities and deck unchanged. |
| Simulator / browser engine | Shared declared-cost dispatch; bot affordability filter. The browser uses this same engine; no duplicate game math. |
| Player aids and printed components | Research price on references, hex Action text and generated player mats. |
| Physical forms and inventory | No change: 82 cards, 153 items, same dimensions and state encoding. |
| Lore | No change. |
| Interface | No new controls or layout. Generated labels reflect the price. |
| Tests | Failing-before cost/affordability regressions, cost/discount checks, complete-game field parity and inference/coverage checks; Research fixture pays the declared cost. |
| Playtest documentation | This receipt records unresolved fairness and required ordinary-rules human observation. Shared historical protocols remain intact. |
| Release | One new 0.24.4 / rules 0.14.0-rc.5-test / engine 0.27.4; historical bundles immutable. |
| Deployment | No deployment. |

## Final implementation and package checks

- All **258 tests passed**, with zero skips or failures, followed by all content,
  boundary, provenance and accounting checks. The first final suite found one
  crash fixture still assuming the old price; its starting Compute now uses the
  declared cost plus one, preserving its original remaining-resource assertion.
  That failed run is retained alongside the passing rerun.
- **96 complete archived candidate games** (16 per backend/player-count cohort,
  selected by seed hash) replayed with exact outcome matches through ordinary
  cost-two execution, without a study rules overlay. The rules and engine
  fingerprints match the sealed package. These are replay controls, not new
  independent balance observations.
- Sealed **0.24.4 / rules 0.14.0-rc.5-test / engine 0.27.4**. Release verification
  passed; historical releases were not changed.
- Built the public-playtest package at clean commit `1916e8072`. Chrome passed
  **13 shipped-engine boundary checks**, then complete desktop (1440×1000) and
  mobile-emulated (390×844) games: tutorial, all four Eras and twelve Headlines,
  scoring, World Ending, actual downloaded export, and linked rules/components.
  No uncaught browser errors or failed requested resources occurred.
- Separate table checks passed full desktop/mobile games, prototype component
  dimensions, and a crowded board with all 20 Orgs and 25 holding cubes.
- No physical-phone or human session occurred. No deployment occurred. The
  remote simulation jobs have finished; existing services were left alone.

Validation logs, browser receipts, exports and screenshots are retained locally
under `evidence/studies/simulation/2026-10-11-final-validation/`. The ordinary
runtime replay is `simulation/2026-10-11-final-runtime-replay.json`.

## Reproduction and retained artifacts

Use the exact source commit named for each comparison. The initial Research runs deliberately evaluate unreleased source and record its live engine fingerprint; they do not claim the old 0.24.3 manifest qualifies new code. Profiles, runtime inputs, seed namespaces, shards and final source identities are bound in the raw reports.

From `games/2038`, unified commands use `node lab/cli/unified-matrix.mjs --runs 6000 --initial-runs 8 --batch-size 24 --workers N --seed ROOT --pre-registration-id ID --rules-configurations FILE --output FILE`. The JSON arms are canonical `{}`, versus exactly one of `{customerPoints:3}`, `{facilityCost:3}`, `{researchComputeCost:2}`. Screening used 12 workers; other broad frames used 8 or 12 as recorded in their execution metadata.

Trained commands use `node evidence/studies/2026-10-11-economy-field.mjs players=N backend=greedy|weighted candidate=equipment3|research2 shard=I shards=S`; S=2 for equipment and S=3 for Research. Canonical source revisions specify the exact root; output files preserve all scenario seeds. Add `smoke=true` for separate rich/batch controls. Analyze with `2026-10-11-economy-analysis.mjs OUTPUT INPUTS...`.

Linux CPU jobs ran in isolated checkouts, without changing the working remote repository or existing services. Node 22.22.1 on Linux; local tests use Node 22.20.0 on macOS. No GPU/model downloads or third-party LLM calls.

Raw archive (local `evidence/studies/simulation/`), hashes below. Analysis-source reconstructions are embedded in the parity and blocked-turn trace artifacts.

| Artifact | SHA-256 |
| --- | --- |
| `2026-10-11-economy-confirm.json` | `615e5380af83411f3442cd787e9c8cc9dadcdb68b9780c8a9407a70abfe9202d` |
| `2026-10-11-economy-equipment3-greedy-3-0.json` | `f3bbe0edcf2e01f8b38c8be04e3975804fd4f6a313eb5e3d3452d8524d2a6a2a` |
| `2026-10-11-economy-equipment3-greedy-3-1.json` | `375fe6fe5aa8e60f2fa57bd56da71a7598feaade17e83c3fa3139e7fa8dc06e0` |
| `2026-10-11-economy-equipment3-greedy-4-0-smoke.json` | `032a632d9dfdcb105b6f6af5c0e4ad802c57e9e36e108d9026d2eac17381bc32` |
| `2026-10-11-economy-equipment3-greedy-4-0.json` | `1f78c10b93065323ebf155a3180cf7d64bd2d00511ccb0347713a87eb65fde17` |
| `2026-10-11-economy-equipment3-greedy-4-1.json` | `87137fa717fbf0fedc8699df75be211411fae7cb4e9422eeb3891059a9fd5868` |
| `2026-10-11-economy-equipment3-greedy-5-0.json` | `55b65743fa80033e23125f70c61c3ddd2edf67d74ef4ae0cbc81c07368880f59` |
| `2026-10-11-economy-equipment3-greedy-5-1.json` | `7b2c00785bef760e7a37505fd13161b57749cd0ef2d2e1955baed9b61a69de06` |
| `2026-10-11-economy-equipment3-weighted-3-0.json` | `17db7687b1518a1a201406ac125d13ec3e9e7ed74790c83bf991bca6e0df48f7` |
| `2026-10-11-economy-equipment3-weighted-3-1.json` | `38b07b6d8d6a6a54cf8f301176ba3536e93c7795f51f4d00f4cd17d961a97324` |
| `2026-10-11-economy-equipment3-weighted-4-0-smoke.json` | `b79d474b36a84251b89ba6fce4efdea97c6443d825dbd294c98aa078c4d8e671` |
| `2026-10-11-economy-equipment3-weighted-4-0.json` | `2eb04daf26aecac73574bcac855599aa9182b66c57c51ea7cd1ab664dc20028d` |
| `2026-10-11-economy-equipment3-weighted-4-1.json` | `2cd7e6d03eb105a7a6cf1cf694dfcb19899af4a41659a3915d001cb8f96c2c36` |
| `2026-10-11-economy-equipment3-weighted-5-0.json` | `b17a929c4843c29048fb25112b7afd36d8df7a3c6e4410b34cdab093b533a191` |
| `2026-10-11-economy-equipment3-weighted-5-1.json` | `5b228ebc9d98521f06398097e09fbb1eafd24706f453d0d5c2877e42a03daf42` |
| `2026-10-11-economy-research2-greedy-3-0.json` | `e8027386cf79c0e21a18cda0fda6e1a48084e96b4d0553882b37fe75d0f5c0a2` |
| `2026-10-11-economy-research2-greedy-3-1.json` | `6b047ede2bf1ca00da9a60d5ca2b00ac4fb93b3934e0a9770b067fabf8791867` |
| `2026-10-11-economy-research2-greedy-3-2.json` | `98d1b82f5ee18010479263f589e78f17f8ebba051d8b8076fea9f893bbfeab5c` |
| `2026-10-11-economy-research2-greedy-4-0-smoke.json` | `4a832376693ba5fd80a6d3f7923308d235c13cd704647c7ab3bbb5dcc65b6486` |
| `2026-10-11-economy-research2-greedy-4-0.json` | `815f524bdc51235383eda0e036611595fa73e5039e6127f9da5327c66f447a6c` |
| `2026-10-11-economy-research2-greedy-4-1.json` | `d764cb7fb25dc63e0c61135acac7f9e66daa26bec8d9715ad37d12265096db03` |
| `2026-10-11-economy-research2-greedy-4-2.json` | `449fd264501a760ba4eb81d663c55e73cbd9542e608b9cc7b86a16ab0d5bb548` |
| `2026-10-11-economy-research2-greedy-5-0.json` | `64aeabd416c9d03d8c093f75ccc6e5cd9cf7f5c45c6c1285590e21ee20eca23b` |
| `2026-10-11-economy-research2-greedy-5-1.json` | `0b5e534f6787ad0c14f2a054f8a7f8e2ec0cba00389bd75dd8230953d8352292` |
| `2026-10-11-economy-research2-greedy-5-2.json` | `eaec169a3ecb542dcdf6f2ac3df761b6a962347fa11e04a8662374b7d82d7aa8` |
| `2026-10-11-economy-research2-legal-greedy-3-0.json` | `67a8da40c177f377a36622d7a231cdd496418411e5cf1891eede5aab861ba8eb` |
| `2026-10-11-economy-research2-legal-greedy-3-1.json` | `4e208922f0d1db0008d54832274c6c5ef30294fb93f6e4992be61355e445d4b1` |
| `2026-10-11-economy-research2-legal-greedy-3-2.json` | `7c693c02adfe89192cccdd4e55ec16790b86d0f6529cf2457b1aa86478ff41c0` |
| `2026-10-11-economy-research2-legal-greedy-4-0-smoke.json` | `911319eb051ae4d36840e1b443a7f69fefd43ac47296ddfcf8bfea02f034aaef` |
| `2026-10-11-economy-research2-legal-greedy-4-0.json` | `d395fdb3066cb75ca45aec3b3c427d3bbdb7214acd965302d846539e11bc7332` |
| `2026-10-11-economy-research2-legal-greedy-4-1.json` | `3ca688616c39e5ac94ba112e1c74691bdeac855db6b396504beb032f09e7882f` |
| `2026-10-11-economy-research2-legal-greedy-4-2.json` | `f4275392a5f224f4ba8834cff4e96c3b9134532dcdf84994ee1f7a1396df0b35` |
| `2026-10-11-economy-research2-legal-greedy-5-0.json` | `1759ee6da3aceb22e1f711bd5e685e8db8d085c334023763f3f9f16300fadff3` |
| `2026-10-11-economy-research2-legal-greedy-5-1.json` | `1cf31087888849b26d9b3ac6a04aeffe523d2aed9e5bc607703563d10c389cdb` |
| `2026-10-11-economy-research2-legal-greedy-5-2.json` | `cf3f4a6e2e1549f1ff6cf02d31a7bca7c3bcd2e739f3175e3ec4f189d3505cb4` |
| `2026-10-11-economy-research2-legal-weighted-3-0.json` | `41ffe239f31b5527d616c838000ad4f2f68d1f831b05e03127bffb6731903a56` |
| `2026-10-11-economy-research2-legal-weighted-3-1.json` | `b3df70fd90dd3e40f2fdf625a2abb5f275e5d6902622d0db9930662f57038031` |
| `2026-10-11-economy-research2-legal-weighted-3-2.json` | `1ec453c6f83170a54c62aabd22ecedec906185907f410171135c57b83f6d6e60` |
| `2026-10-11-economy-research2-legal-weighted-4-0-smoke.json` | `b387ca89f1e0050d45c22a5dad345b04657e580a701005fe4d571a6c0771c602` |
| `2026-10-11-economy-research2-legal-weighted-4-0.json` | `6eb700180e9d4f2eab595ecdb52660bd981677788b93bc0e03da640b2c20b6a9` |
| `2026-10-11-economy-research2-legal-weighted-4-1.json` | `222022061e973f880157384acc9301d3be0636bebce04cf76ed88d480036d426` |
| `2026-10-11-economy-research2-legal-weighted-4-2.json` | `a1f08e00671296c4cc0cde8133ff96945b09d089cccb91f6e41e537a80cf2882` |
| `2026-10-11-economy-research2-legal-weighted-5-0.json` | `2ad3988be231ed7b4dab7c6d640bc20810c803156c65d590090c620e0980bae0` |
| `2026-10-11-economy-research2-legal-weighted-5-1.json` | `ef0ea20c175f3b8cd80713225754c93b194924e090d85131fc5c7a36b20f3a2b` |
| `2026-10-11-economy-research2-legal-weighted-5-2.json` | `43b501cde9875c4e5c38adf84ba199d08d0e0325c573543c36e7c156b56197c1` |
| `2026-10-11-economy-research2-weighted-3-0.json` | `c36c5d7276ac0ddd04ce6f5879098d4598aff6aeef7f73702ef85f93b167e75a` |
| `2026-10-11-economy-research2-weighted-3-1.json` | `86ac457e1687b3411f667adae148d68c199369ed88a27eb9f032bd6ce1d457f8` |
| `2026-10-11-economy-research2-weighted-3-2.json` | `a53d550a0d36d25a1e1850fd93221164de3b162920ca8ead0492003264b5c8f2` |
| `2026-10-11-economy-research2-weighted-4-0-smoke.json` | `9c7732ecc0fd42d7a258140a2f8bdb6993f374ce338bf188956cf09e813c153e` |
| `2026-10-11-economy-research2-weighted-4-0.json` | `bbbdd5a298cde48c3b022a6d615e5c0e38df7b2a9f1e1df7f7bec3440bde9ec1` |
| `2026-10-11-economy-research2-weighted-4-1.json` | `8a274cc0777100c83f332f188899650e59f2c9a0c280ff23d47b79277334c5fc` |
| `2026-10-11-economy-research2-weighted-4-2.json` | `b99b401edb4d08f1e50888a0bfba3f43450d9a609f5b60e315429494be37cf66` |
| `2026-10-11-economy-research2-weighted-5-0.json` | `25e1820746d069c33c712e3506c0253f2fbcedf61a2edf81ae6bf797a7090c2a` |
| `2026-10-11-economy-research2-weighted-5-1.json` | `7f705c178b3365d3e44642c3754ab8dad2c680352812795682dc16c3a9a7e32e` |
| `2026-10-11-economy-research2-weighted-5-2.json` | `f8542df2049b396dd8ebf6eb84669b05a4060e201bb24c53103fe051dbf7602a` |
| `2026-10-11-economy-screen.json` | `dbb6f4f5cf8cf1e28469a84e3c9daa6d43d86ca02f518427cc8d4968e4670b61` |
| `2026-10-11-equipment-trained-analysis.json` | `15a31783d0ab1206a865382105296fbbad8e1f0b2f9049d4787f6a42e62a1955` |
| `2026-10-11-research-confirm.json` | `1bf88f543628bd2932bb909a509a6c0e810191e4ce93522e9ccd8faa4798ad0a` |
| `2026-10-11-research-cost-one-parity.json` | `8427cbd342a7bad76b23cbb8fe25663f57e4ef6abbe4bc9be4c0afe6f6bcf432` |
| `2026-10-11-research-legal-analysis.json` | `5136d7a33dd9fad23bd32314a511bab96a89a747698f55872f6055c870816596` |
| `2026-10-11-research-noop-trace.json` | `870f20ce2140b24594f5162e6bf19c4ed1716d78ec6d05c7429bb1a9d4521844` |
| `2026-10-11-research-screen.json` | `e07f03348a98e6b5d4d6d4174a790668307e36731717577dc3b6762c3cc734ea` |
| `2026-10-11-research-trained-analysis.json` | `ec5ff5d2082ccd3fb4088904217a4f28803de3fd5045e5c3ae43e01074cabbf2` |
| `2026-10-11-research-legal-audit.json` | `b2540d08d95f53916497d7ea2eb24f0c764c0c7f1188bf4b46a1ac573d369936` |
| `2026-10-11-final-runtime-replay.json` | `6f22ce5111c6dbe285e98eed7e1588d48b6f0549341375f68cc02a723f59f25b` |
| `2026-10-11-final-validation/browser/browser-receipt.json` | `77f61c33cd105664efa8dd81491c8893fce663866cf3368291a239846f4c2a33` |
| `2026-10-11-final-validation/tests.log` | `bc375e4dd7ea0aef00d5211b27dbc88222ade0ebbc0826add9a6586ef4f7b812` |
| `2026-10-11-final-validation/content-check.log` | `f836dc6c0e598f0b9a966b51a3b2b1594bc499a374802a242c0e61cfe81d9041` |
| `2026-10-11-final-validation/table-browser.log` | `438758284fd1e95e62058b73505a3c006cad04eb3dd901448792d5358b190814` |
| `2026-10-11-final-validation/tests-before-fixture-fix.log` | `eda035444065ac6d1824f38ead4ff023275ff64e27aaca799e08e78f40ba58aa` |

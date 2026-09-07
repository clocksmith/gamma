# Six Headlines per Era — implementation evidence

The requested expansion is implemented in executable **0.19.8**, physical
candidate **0.11.0-rc.10-test**, engine **0.22.1**. The deck has six Headlines per
Era and still reveals three per Era. Its original sixteen card records and all
seven original supplied vignettes are unchanged (see `preservation.json`).

The eight additions are Human-Original Guarantee; The Last Plumber Boom;
Wartime Water Bridge; Cognitive Donor Clinics; The Human Signature; Analog
Havens; Biological Colocation; and Limb Liquidity. Rules live in the component
records; creative copy and scenario policies live in the existing world bible.
The runtime, reference, gallery, and physical inventory include all twenty-four.
There are 114 standard cards plus six foldouts, 120 printed pieces in total.

## Verification

`npm run build:all`, `npm run check`, `npm run game:release:verify`, and
`npm test` pass. The final suite reports 304 passing tests and no failures or
skips. The focused regression covers all eight effects and routes their choices
through the actual browser decision contract at two, three, four, and five players.
It checks consent before payment/movement, declined offers, contributions and
refunds, normal Customer requirements, immediate Customer Mandate, capped resources,
permanent Trust awards, preserved Agent ownership, and no extra action usage.
The full suite also checks deterministic complete games with twelve Headline reveals.
This is automated functional evidence, not a human playtest or a balance study.

## Retained failures

`initial-tests.log.gz` records 300 passes and four failures: new cards were omitted
from the explicit card-reference layout, and two old assertions assumed the earlier
inventory. `initial.patch.gz` plus `initial-headline-test.mjs.txt` reconstruct that
working change after decompression against the base commit in `verification.json`.

`pre-scoring-tests.log` records 304 passes before a separate review found a real
scoring defect. `scoring-failure.log` proves that certification added a Customer
without immediately recording its Mandate award. The earlier sealed 0.19.7 / rc.9
artifacts remain intact. The current 0.19.8 / rc.10 candidate synchronizes the
award inside the Headline; the regression now requires it before selection.
The passing earlier suite is not evidence that this boundary already worked.

## Scope and next evidence

No shared Fusion/AGI/Quantum mechanic, new resource, permanent Headline modifier,
extra action, or secret player was added. The eight numerical effects are provisional
playtest implementations of the requested expansion. Their clarity and strategic
value require human observation. No new publication or deployment occurred.
`verification.json` identifies the sealed release and hashes the changed source
files and retained logs. Generated local review and kit outputs remain in `dist/`.

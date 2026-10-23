# bits80-bridge-v1: frozen design (BITS bridge on the live 80-problem slots)

Owner Amendment 2 (2026-10-22, relayed from Mars): after the minify-only control and the
structural stage, evaluate eligible candidates on the live 80-problem profiles against the
current gates in [BITS_PROMOTION.md](../BITS_PROMOTION.md), and report promote or not per width.
Keep that decision separate from the 500-problem M1 result. Do not restart the older 80-problem
experiment, and do not deploy to BITS or 256one without the owner's go-ahead.

This design was committed before any candidate was evaluated on the 80. It is an evaluation
only: no search, refit or new source.

## Slots and gates (unchanged)

| Slot | Live profile | Selections | Package bytes | Selection bar (≥2% below) | Package bar (≤5% above) |
| --- | --- | ---: | ---: | ---: | ---: |
| JavaScript 80, literal, 7-bit, primitive | `bits-literal-joint80-7-v2` | 9,910 | 12,798 | ≤ 9,711 | ≤ 13,438 |
| JavaScript 80, literal, 8-bit, primitive | `bits-literal-joint80-8-v2` | 6,161 | 11,750 | ≤ 6,037 | ≤ 12,338 |

**Sources.** The same 80 compact sources the live profiles encode: SHA-256 per problem from
[published-8-v1-sources.json](../guides-joint80-8-v2/published-8-v1-sources.json), loaded from
`scale-v2/generated` and hash-checked. Only these have publication permission (gate 2). The
shared-style rewrites of the 80 are not published, so they are not eligible sources here.

## Candidates

Every 128- and 256-entry literal dictionary from a frozen experiment whose results are committed
(gate 1):
- style150-v1 run-v1: A, A0, B, C, D, E, CH, DH;
- style150-v2 run-v2: C, D, E, CH, DH;
- scale500-v1 run-v1: W1, W2, H1, H2, I2-s1 to s5;
- minify-control-v1 run-v1: the O, Om and R dictionaries, F500 and Fdev;
- structural-v1 run-v1: the L arms only, after its results are committed.

Typed (T) dictionaries are excluded because the slots require the canonical codec. Each
candidate runs at its own width: 128 entries on the 7-bit slot, 256 on the 8-bit slot.

**Controls.** The live dictionaries themselves must reproduce 9,910 / 12,798 and 6,161 / 11,750
exactly. If they do not, the evaluation is invalid.

## Evaluation

For each candidate:
1. Exact canonical parse of the 80 sources, giving selections and complete package bytes
   (LTD1 dictionary plus LTV1 packets with 41-byte headers, the live accounting).
2. Every packet written and decoded through the canonical codec to its source hash.
3. Macro classification of every entry with 256one `public/labs/two-button/macro-entries.js`
   (`macroDefinitions`, read-only).
4. The whole-program literal check.
5. The per-problem distribution against the live profile: fewer, same, more, median and range.

**Decision per width.** A candidate passes gates 1–3 if it:
- is primitive;
- decodes all 80;
- is at or below the selection bar;
- is at or below the package bar.

If one or more pass, the width's candidate is the one with the fewest selections (ties broken
by package bytes). It is reported as **eligible**. Gates 4 (an independently verified guide
package) and 5 (BITS tests and replay) come next, and deployment waits for the owner. If none
passes, the width is **not promoted**.

## Predictions

- **B1:** the live controls reproduce exactly.
- **B2:** no candidate meets the 8-bit bar. Every candidate was fitted on other sources or
  other cohorts, and the live 8-bit dictionary was searched on these 80 sources.
- **B3:** no candidate meets the 7-bit bar.

## Not claimed

No deployment. This makes no M1 statement: the 80-problem slots are separate from the frozen
500. No coverage or solving claim.

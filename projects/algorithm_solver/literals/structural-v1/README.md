# structural-v1: typed, parameterized components on dev-val (negative result)

Frozen design: [FREEZE.md](FREEZE.md) and [contract.json](contract.json) (commit `98cf5b8f9`).
Public evidence: [evidence/results.json](evidence/results.json), written by
[evidence.py](evidence.py). It holds per-arm aggregates, per-problem counts, dictionary hashes and
the dev-fit audit counts. Sources, dictionaries and sequences stay private. All 12 arms ran on
Jupiter in 494 s.

**Launch ordering, disclosed.** A staging error made the run start a few seconds before the freeze
commit landed. No arm had finished when that commit was pushed. The run checks every pinned file
by SHA-256 against contract.json, and the committed files are those files. Nothing changed after
launch.

## Result

Typed components do not improve these representations. Each dictionary was fitted on dev-fit
300 and measured unchanged on dev-val 100:

| dev-val 100 | L (literal) | T (literal + typed components) | Change | Per problem (fewer / same / more) | Components kept by search |
| --- | ---: | ---: | ---: | --- | --- |
| O, 256 | 30,426 | 30,426 | 0 | 0 / 100 / 0 | none |
| Om, 256 | 27,098 | 27,098 | 0 | 0 / 100 / 0 | none |
| R, 256 | 8,948 | **8,937** | −0.12% | 33 / 16 / 51 | C1 map increment, C8 count table |
| O, 128 | 49,690 | 49,690 | 0 | 0 / 100 / 0 | none |
| Om, 128 | 41,394 | 41,394 | 0 | 0 / 100 / 0 | none |
| R, 128 | 14,014 | 14,121 | +0.76% | 28 / 18 / 54 | C1, Q7 push |

On the original and minified sources, the search deleted every component and END and returned
exactly the literal dictionary. On the rewrites at 256 entries it kept two counting components
and END. Those are used 19 times on dev-val, and they cut 11 selections in total, while more
programs got worse than better (median +1). At 128 entries the typed arm ended 0.76% worse. The
components took slots from literals, and the search settled at a different local optimum. Package
bytes are higher for T in every pair once the 3,986-byte decoder is counted. On R they are higher
even without it (15,398 vs 15,255 at 256), because the component block is stored.

**Why.** The audit had already shown thin support: 4, 10 and 19 admissible components on O, Om and
R. Where an idiom recurs often in the rewrites, the shared style has made it fixed text, so a
single literal entry covers it in one selection. The typed form costs at least four: the
component, each operand and END. A component helps only where the operands vary and the fixed text
is long. Graph and tree idioms, the cases with long skeletons, occur in at most 7 dev-fit problems.
On O and Om, fixed text rarely matches, because spacing, `const` and other phrasings vary.

## Predictions (scored as frozen)

| | Prediction | Outcome |
| --- | --- | --- |
| E1 | at 256, T-R below L-R on dev-val, by less than 5% | **Met, at noise level.** −0.12% (8,937 vs 8,948), with 51 of 100 programs worse |
| E2 | at 256, T's relative reduction largest on R, then Om, then O | **Not met.** R −0.12%, Om and O both 0% |
| E3 | L arms reproduce minify-control-v1's Fdev arms exactly | **Met.** All six identical (49,690, 41,394, 14,014, 30,426, 27,098, 8,948) |
| E4 | T package bytes with decoder above L in all 6 pairs | **Met** |
| E5 | no arm meets M1 on dev-val | **Met.** Best median 63.5 |
| E6 | every packet decodes | **Met.** 1,200 packets (T through decoder.mjs, L through the canonical codec) |
| E7 | T-R-256 keeps components from at least 3 of 4 families | **Not met.** Counting only (C1, C8) |

## Decision under the frozen selection rule

- **256 entries:** the rule selects T-R-256. It has the fewest dev-val selections and beats L-R-256,
  but only by 11 selections, which is smaller than the per-problem spread (−19 to +9). Its package
  is larger with or without the decoder, and 51 programs get worse against 33 better. I do not
  propose confirming it. Under the freeze, confirmation is a separate step that needs the owner's
  decision. The final held-out 100 stays closed.
- **128 entries:** the rule selects L-R-128. That is a literal dictionary, identical to
  minify-control-v1's dev-fit arm, so the typed representation does not qualify.

## What this means for the direction

- This component family does not move M1. On dev-val the best arm is still at median 63.5 and p95
  211, against 32 and 96, with 55% single-character selections against 10%.
- The binding cost is operand charging. In the shared style, most selections go to identifiers,
  operators and short expressions inside statements, and a component still charges all of them.
- Structure would need to reduce operand cost, not skeleton cost. Two examples:
  - binding identifiers once per program and referring to them by role;
  - typed expression constructors over the operators that make up the single-character tail.

  Either would be a new frozen design under goal 2c. Neither has been tested.
- No scorer: there is no search headroom to rank. Every arm stopped at a local optimum well under
  its cap.

Not claimed: M1, M2 or M3, assembly, or a BITS profile. A typed codec cannot enter the
canonical-codec literal slots.

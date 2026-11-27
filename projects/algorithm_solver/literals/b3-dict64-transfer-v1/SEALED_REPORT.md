# B3 Sealed Transfer Report: Frozen 64-Entry Dictionary & Guarded Rewriter

## Frozen Pre-Unseal Pins Verified

- `artifacts/frozen_dict64.json` SHA-256: `70166bd0f6b84af31ab9bc5479cab5bae50b6fe3bb000fdeca85b8e0bb87c135` (unchanged from matched80 witness and dev transfer)
- `rewriter.mjs` SHA-256: `6bd15a99a6f8c2dda791646504fc8922843b1f4f24ac3808dc854599edac814b` (commit `174e895d8`, carrying O(1)-step sealed numeric copy-sort domain guard verified by NC4 16/16)
- Step ceiling: `1.1x` deterministic instrumented steps; minimum transfer coverage bar: `90.0%`; zero wrong acceptances required.
- Zero overlap with `matched80` (80) or `dev_transfer` (83); zero edits or refitting performed on sealed problems.
- **B4 Gate:** `B4` remains **PAUSED** pending explicit model-compute authorization.

## Sealed Transfer Verdicts by Slice (`B3H1` Huffman vs `B3P1` Fixed-6-Bit)

| Slice | Accepted / Total | Coverage | Wrong Acc | Max Step Ratio | `B3H1` Complete Bits (vs Frozen BPE-255 Huff) | `B3H1` Verdict | `B3P1` Fixed-6 Complete Bits (vs Frozen BPE-255 F8) | `B3P1` Verdict |
| --- | --- | ---: | ---: | ---: | --- | --- | --- | --- |
| `sealed_reserved` | **40/48** | **83.33%** | 0 | 1.0761x | 123,184 vs 152,584 (-29400) | **`FAIL`** | 135,504 vs 184,488 (-48984) | **`FAIL`** |
| `sealed_fresh_authored` | **50/87** | **57.47%** | 0 | 1.0889x | 374,936 vs 410,800 (-35864) | **`FAIL`** | 399,088 vs 508,352 (-109264) | **`FAIL`** |
| `sealed_combined` | **90/135** | **66.67%** | 0 | 1.0889x | 476,416 vs 559,816 (-83400) | **`FAIL`** | 513,408 vs 689,424 (-176016) | **`FAIL`** |

## Refusal Reasons & In-Domain BPE-256 Comparators

- **`sealed_reserved`** (48 problems, 591 frozen tests, 40,320 raw B): refusals={'step_ceiling_exceeded': 4, 'unspellable_zero_escape': 4}, `B3H1` excl. dec=`107,576` b + dec=`15,608` b, in-domain BPE-256 Huff=`121,424` b, frozen original BPE-255 Huff=`155,656` b.
- **`sealed_fresh_authored`** (87 problems, 1,095 frozen tests, 105,629 raw B): refusals={'unspellable_zero_escape': 24, 'behavior_or_runtime_mismatch': 10, 'step_ceiling_exceeded': 3}, `B3H1` excl. dec=`359,328` b + dec=`15,608` b, in-domain BPE-256 Huff=`339,376` b, frozen original BPE-255 Huff=`414,272` b.
- **`sealed_combined`** (135 problems, 1,686 frozen tests, 145,949 raw B): refusals={'step_ceiling_exceeded': 7, 'unspellable_zero_escape': 28, 'behavior_or_runtime_mismatch': 10}, `B3H1` excl. dec=`460,808` b + dec=`15,608` b, in-domain BPE-256 Huff=`466,064` b, frozen original BPE-255 Huff=`566,848` b.

## Sibling Same-Realm Copy-Sort Audit (`b3-copy-sort-audit-v1/check.mjs`)

- Independently checking the frozen guarded rewriter (`rewriter.mjs` SHA-256 `6bd15a99a6f8...`) against `../b3-copy-sort-audit-v1/check.mjs` (16 same-realm adversarial cases) yields **13/16 PASS, 3/16 FAIL**:
  - Passes all 13 checks for ordinary finite numbers, wide `Number`, sparse holes, signed `-0`, `BigInt`, and mixed strings across both `slice` and `spread` forms.
  - Fails 3 remaining same-realm edge cases: indexed getter double-read on fallback (`slice` and `spread`, reads=2 vs 1) and `Array` subclass `Symbol.species` constructor preservation (`slice`, returns `Array` instead of `Alt`).
- Because this sealed transfer run has already been scored and failed coverage (`< 90%`), `rewriter.mjs` is left frozen post-unseal; both the coverage failure and this 3/16 same-realm audit finding stand together as the record against advancing `B3` to `B4`.

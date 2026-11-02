# Native-ABI and pure-core contract (v1, 2026-11-02)

Applies to the two development cohorts executed here
(`requested-243-370-35-20261028-v1`, `requested-156-1940-31-20261028-v1`) and to
modules loaded through `run-case.cjs`. Qualification stays `unknown`; nothing here
admits, promotes or qualifies a source.

## Design rules

1. **Canonicalization is not minification.** Deterministic formatting and
   scope-aware naming are separate from one-letter identifiers or one-space
   compression. Compact palettes remain a separate, measured projection experiment
   on a small development slice. They never silently rewrite receipt-bound module
   bytes and never act as a catalogue qualification gate. Composition stays paused
   (see [GOALS](../../../../GOALS.md)).
2. **Syntax-aware transforms and revisioned namespaces.** Module and dependency
   transforms must be AST-aware and preserve `'use strict'`, imports and helper
   semantics. Any future multi-module composition namespaces each entry by problem
   ID and revision/hash (`solve_<id>_<rev>`), never by problem ID alone. No
   composition is implemented or resumed by this contract.
3. **Pure core and native adapter, with charged costs.**
   - `solve(...)` is the pure value-domain entrypoint: semantics declare
     `solve_effects: {"inputMutation": "forbidden", "outputAliasing": "forbidden"}`.
   - `<nativeMethod>` / `Solution.<nativeMethod>` implements the official LeetCode
     ABI, including in-place mutation where the problem specifies it
     (`native_effects`, `official_interface.in_place_arg`).
   - Any copy or representation conversion made by `solve` or by the native adapter
     is charged in the semantics `complexity_target` and `charged_costs`, not hidden
     in an uncharged adapter. Source bytes are charged as written.
4. **Honest checker scope.** [`check_native_abi.py`](check_native_abi.py) enforces
   module export shape, representation-specific mutation/alias checks, non-BMP
   string canaries and hash-supersession lineage. It is a regression gate over
   declared contracts, not a formal proof of purity and not a replacement for
   independent catalogue qualification.
5. **Catalogue counts (verified 2026-11-02 from the files named).**

   | Source | JavaScript | Python |
   |---|---|---|
   | `ALL4081-STATUS-v1.json` qualified (frozen-admitted-typed-effects) | 400 | 372 |
   | `ALL4081-STATUS-v4.json` qualified | 400 (380 frozen + 20 normative) | 392 (372 frozen + 20 normative) |
   | `private-recovery-20261026/qualified-sources/owner-artifacts/sources/` files on disk | 518 | 518 |

   The on-disk files include unpromoted recovery files alongside the admitted
   subset. `875.js` is already qualified (`public-domain-qualification-v3`,
   `QUALIFICATION-SUMMARY-v1.json`, SHA-256 `1add759c…`); 156, 280, 340 and 903 are
   in the unqualified 66-problem development cohorts.

## Implementation guards (as applied)

| Step | Component | Guard |
|---|---|---|
| 1 | `run-case.cjs` | `fn = typeof candidate?.solve === 'function' ? candidate.solve : candidate`. `875.js` (`{ solve, Solution, minEatingSpeed }`) now loads without editing its qualified bytes; the previous loader failed with `candidate is not a function`. Modified development modules end with `if (typeof Solution !== "undefined") solve.Solution = Solution;` so pure-only modules never throw on load. |
| 2 | 156 | `solve` deep-copies a native `TreeNode` graph (iterative, seen map rejects a node reached twice) before rotating, so it neither mutates nor aliases caller nodes (the previous `solve` returned all 5 caller nodes on a 5-node tree). `upsideDownBinaryTree` / `Solution.upsideDownBinaryTree` rotates in place under `native_effects.mutates_inputs: true`. Copy charged: O(n) time, O(n) space. |
| 3 | 280 | `wiggleSort` writes the result into `nums` in place (`nums[:] = solve(nums)` in Python, element-wise copy in JavaScript) and returns nothing. `official_interface.in_place_arg: 0` is declared in `contracts.json` and both semantics. `run_candidates.py` requires `args_after == args_before` and `result == expected` for `solve`, and `args_after[0] == expected` with other arguments unchanged for the official entry, on every case including mutating ones. |
| 4 | 340 | Semantics pin `string_unit: unicode_codepoint`; JavaScript iterates `Array.from(s)`. Canary rows use oracle-computed expected values. The proposed `("\u{1F600}a", 1)` row expects **1**, not 2, and does not tell code points from UTF-16 units. The added rows `("\u{1F600}\u{1F600}a", 1)` and `("a\u{1F600}b\u{1F600}", 2)` expect 2 and 3, where UTF-16 units give 1 and 2. |
| 5 | 903 | `manifest.json` `source_inventory` and `authoring-catalog.json` now carry the corrected hashes (`5bbc2828…` Python, `88ab1b44…` JavaScript). The pre-fix hashes, prior catalog variant IDs, freeze amendments and history blobs are recorded under explicit `supersedes` entries. Historical blobs stay in `study-history/blobs/`. |

[`revise-cohort-lineage.py`](revise-cohort-lineage.py) performed the rebinding
(freeze amendments, blob archiving, inventory/catalog `supersedes`, `SHA256SUMS`).
Running it again with no byte changes does nothing. The catalog's original
variant-ID generator is not recorded in this repository, so prior IDs are kept
verbatim. Revised IDs follow the rule stated in each catalog's
`variant_id_rules`.

## Remaining boundaries

- 286 (Walls and Gates) still returns a new grid; its official in-place ABI is not
  implemented or tested.
- The native-ABI split covers 156, 280 and 340 only; the other 63 cohort problems
  keep their existing wrapper semantics. Export shape is checked for all 66.
- Official-domain maxima, independent qualification and serving admission remain
  open.

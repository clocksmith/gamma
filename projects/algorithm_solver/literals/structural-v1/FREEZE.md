# structural-v1: frozen design (typed, parameterized components)

Owner direction of 2026-10-22 with Amendment 1 (relayed from Mars): after the compaction
control, test a small set of typed, parameterized components on a development-validation
partition. Audit every parameter, callback, constant table, helper and dispatch rule, charge
their complete representation, and reject problem-ID lookup or uncharged payloads. M1
thresholds are unchanged. This is goal 2c (structured and parameterized languages): a separate
representation with its own charged semantics. It is not a flat-literal result, and an offline
representation result says nothing about M2 or M3.

This design replaces the draft, which was committed as `71fd3d4b5` and never frozen or run. It
was written after [minify-control-v1](../minify-control-v1/README.md) reported (`51b0f434e`) and
before any structural arm ran. The implementation, audit and inputs are pinned in
`contract.json` in the same commit or a later one, before any arm runs. A 200-trial smoke run
checks the plumbing first; its output is discarded.

## Cohort, pools and partition

- **Problems and pools:** minify-control-v1's pools (one source per problem, pinned there by
  hash) on the frozen 500:
  - O: admitted originals;
  - Om: terser-minified originals, 500/500 qualified;
  - R: shared-style rewrites.
- **Partition:** minify-control-v1's split of the scale500 training 400. Every arm fits on
  **dev-fit 300** and is measured unchanged on **dev-val 100**.
- **Final held-out 100** (scale500 split): **not opened in this stage.** Its sources never
  pass through the matcher, and no measurement includes it. Using it needs a separately frozen
  confirmation step and the owner's decision.

## Representation

- **L:** the canonical flat-literal codec, unchanged.
- **T:** L plus typed components from [components.json](components.json) and one END code, all
  inside the same 2^w budget. There are 31 components in four families:
  - counting, C1–C9;
  - queue and stack operations, Q1–Q7;
  - graph traversal, G1–G9;
  - tree folds, T1–T7 (T7 is a list walk, the unary fold).

  Each component states its holes, guards, inputs, effects, aliasing and numeric domain.

**Expansion.** A component code is followed by one operand per distinct hole, in first-use
order.
- An `id` operand is exactly one identifier-shaped literal selection.
- `pure`, `expr` and `stmts` operands are codes (literals and nested components) closed by END.
- The decoder writes the template's fixed text with each operand's decoded bytes in place, and
  repeats them for a hole named twice.
- Expansion is byte-exact. There is no whitespace insertion, renaming, default operand or hidden
  helper.
- Nesting depth is at most 8, and every code consumes a field, so decoding terminates.

Each decoded program must equal its qualified source byte for byte (SHA-256).
[decoder.mjs](decoder.mjs) checks every T packet, independently of the Python encoder in
[typed.py](typed.py).

**Matching** ([matcher.mjs](matcher.mjs)) uses the acorn 8.16.0 AST, the system package at
`/usr/share/nodejs/acorn`, pinned by its package hash, with `preserveParens`.
- `id` holes cover exactly one Identifier.
- `expr` and `pure` holes cover exactly one expression node, and `pure` holes contain no call,
  `new`, assignment, update, `delete`, `await` or `yield`.
- `stmts` holes cover a contiguous run of zero or more statements of one block.
- The fixed text must match the source bytes exactly, and the whole match must be the
  component's declared node kind.
- Guards: C1–C5 require a Map binding and G4 a Set binding (name-level, not scope-resolved, as
  disclosed); a T7 body may not reassign its pointer; the single-if components (G3, G4, T1) must have no `else`.

**Whole-solution exclusion.** A match is not admissible if its free bytes are at least half of
its program. Free bytes are fixed text plus repeated-hole copies, which operands do not charge.

**Charging.** Every code is one w-bit selection: literal, component and END codes alike.
Operands are charged for all their codes:
- identifiers;
- constants;
- sub-expressions;
- nested components;
- END where their type needs one.

Wrappers (function headers, `solve`, constructor lines) and dependencies (helpers, and the Map
or Set declarations a guard requires) are ordinary program text, charged where they occur.

The T dictionary is the LTD1 list of every code's bytes plus an LTC1 block holding the used
components' templates and hole types. T packets mirror LTV1 framing (41 bytes: magic, width,
dictionary hash, count). Package bytes are reported without and with the decoder's 3,986 source
bytes; the canonical literal decoder is not charged, as in every earlier experiment.

**Parse.** The parse is the minimum number of codes over literal edges and admitted component
instances, recursing into operand spans, memoized by span and depth. Within admitted matches it
is exact. It is not a semantic optimum.

## Audit (Amendment 1)

Every component has been checked for each item. No component is disguised, problem-specific or
uncharged.

| Item | Finding |
| --- | --- |
| Parameters | Every hole is typed; every operand is charged code by code; no default operands. |
| Callbacks | No callback holes. G1's fixed `()=>[]` is stored template text allocating fresh empty lists, charged in dictionary bytes. |
| Constant tables | G5 and G6 direction lists (four unit offsets), C9's 26 and 97 (lowercase alphabet), C8 and G9 fill values 0 and false: general constants stated in the contracts and stored in the dictionary. |
| Helpers | None. No component expands to or requires an unlisted helper; required declarations are program text. |
| Dispatch rules | None. No component selects behavior by problem identity or input. |
| Problem-ID lookup | None. Expansion and guards read only the source's AST and bytes. |
| Uncharged payloads | None beyond fixed template text (in the dictionary) and repeated-hole copies, which the whole-solution exclusion bounds. |

**Cross-problem reuse.** The audit ([measure.py](measure.py) `audit`, dev-fit 300 only, sha
`06fbd888...`) admits a component for a pool only if it has admissible matches in at least 2
dev-fit problems of that pool. That leaves:
- O: 4 components (C6, C7, G9, Q7). Formatting blocks most fixed text.
- Om: 10 (C1, C3, C5, C6, G1, G3, G9, Q3, Q6, Q7).
- R: 19 (C1, C3–C8, G1–G3, G9, Q1, Q3, Q5–Q7, T1, T5, T7).

The most supported are Q7 push (101, 42 and 89 problems in O, Om and R), C8 count table (24 in
R), C5 map get-or-zero (18 in R) and C1 map increment (16 in R). Graph and tree components reach
at most 7 problems.

## Arms (12)

Each pool (O, Om, R) is crossed with each representation (L, T) at both widths (128 entries / 7
bits and 256 / 8):
- Fit on dev-fit 300; measure unchanged on dev-val 100.
- Start from the 96-character alphabet. T arms also start with END and the pool's admissible
  components.
- Greedy refill (shortlist 24), then matched80-v3 exact local search with the scale500
  neighborhood, a 60,000-trial cap, a 6 h safety limit and `PYTHONHASHSEED=0`.
- L proposes mined chosen-source spans only, exactly as minify-control-v1.
- T proposes the absent admissible components first, then the same span mining restricted to
  text-contiguous literal runs. Search may delete components and END, and re-add them.

L arms must reproduce minify-control-v1's Fdev arms exactly (same procedure, delegated parse).

## Metrics (M1 thresholds unchanged)

Per arm on dev-val 100:
- selections (all codes), median, p95, worst;
- programs within 32 and within 96 selections;
- the single-character selection and byte fractions;
- component and END code fractions;
- dictionary bytes;
- package bytes without and with the decoder;
- trials and stop reason;
- per-component uses;
- per-problem counts.

Every packet is decoded; one failure fails the stage.

## Predictions

- **E1:** at 256, T-R uses fewer dev-val selections than L-R, but less than 5% fewer.
- **E2:** at 256, T's relative reduction over L is largest on R, then Om, then O. Support
  follows the same order in the audit.
- **E3:** every L arm reproduces the dev-val selections of the matching minify-control-v1 Fdev
  arm exactly.
- **E4:** in all 6 pool-and-width pairs, T's package bytes including the decoder exceed L's.
- **E5:** no arm meets M1 on dev-val (median above 32).
- **E6:** every packet decodes; zero failures.
- **E7:** the T-R-256 final dictionary keeps components from at least 3 of the 4 families.

## Selection rule (frozen before any confirmation)

At each width, the candidate for any later confirmation is the arm with the fewest dev-val
selections, with ties broken by package bytes including the decoder. A T candidate goes to
confirmation only if it beats the L arm of its pool. Confirmation (the final held-out 100 or a
new protected cohort) is a separate frozen step that needs the owner's decision.

## Not in this stage

- No learned scorer and no training. A scorer needs stronger conventional search to show
  headroom first, and training needs explicit approval.
- No bit/hex model, no 400-step run and no BITS profile. A typed codec is not the canonical
  codec, so it cannot enter the live literal slots.
- No M2, M3 or assembly claim.

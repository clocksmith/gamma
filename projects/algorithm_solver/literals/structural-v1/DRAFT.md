# structural-v1: draft design (typed, parameterized components)

**Draft, not frozen.** Owner Amendment 1 (2026-10-22) orders the minify-only control
([minify-control-v1](../minify-control-v1/FREEZE.md)) first. This draft is re-checked against
the control's results, then frozen in its own commit before any of its arms run.

Owner direction of 2026-10-22, evening (relayed from Mars): make the representation better
with a small set of typed, parameterized components on a cleared development cohort. Charge
every operand, identifier, constant, wrapper and dependency. Compare original sources,
rewritten sources, dictionary changes and their combination. Keep the M1 thresholds. This is
goal 2c (structured and parameterized languages): a separate representation with its own
charged semantics, not a flat-literal result.

When frozen, this design and [components.json](components.json) are pinned before any of their
arms run, and the implementation is pinned by SHA-256 in `contract.json`.

## Cohort and exposure

- **Population:** the frozen 500 ([population-500.json](../admission500-v1/evidence/population-500.json),
  sha `0d6cb3ff...`), the M1 population. All of it is cleared, exposed development data. The
  protected 66 stay closed.
- **Design cohort:** the 400 training problems of the scale500 split (sha256
  `scale500-v1-heldout` + id, lowest 100 held out). Before this freeze, regular-expression
  counts and excerpts of the training 400's shared-style sources were read to choose the
  component text (disclosed here). No held-out source was read.
- **Development-validation partition (Amendment 1):** component comparisons use the
  minify-control-v1 split of the training 400. That is dev-fit 300 and dev-val 100: sha256
  `minify-control-v1-devval` + id, lowest 100 to dev-val. Component and dictionary choices may
  be compared on dev-val repeatedly.
- **Final held-out 100:** not reopened for component comparisons after any component change.
  It is measured once, after components, dictionaries, search procedure and selection rule
  are frozen. scale500 exposed it as development data, so it is still not a sealed
  confirmation. A separately protected confirmation cohort needs newly authored problems and
  an owner decision.

## Sources (one per problem, all 500)

| Pool | Source | Qualification |
| --- | --- | --- |
| O | the admitted original (`population500/<id>.js`) | existing baseline, 48,405 cases |
| Om | O minified by terser 5.46.1 (`compress:false, mangle:false`, comments dropped): compaction only, same names and algorithm | strict parity on all frozen cases, as for rewrites. A failing Om falls back to O for that problem, is recorded, and stays in the denominator |
| R | the shared-style rewrite (style150-v1 for the first 150, scale500-v1 for the other 350) | already qualified, 500/500 |

Om is the compaction-only control that scale500-v1 lacked. It separates shared style from
plain compaction.

## Representations

- **L (literal):** the canonical flat-literal codec, unchanged. The dictionary has at most
  2^w entries, including the 96-character fallback alphabet.
- **T (typed):** L plus typed components from [components.json](components.json) and one END
  code, all inside the same 2^w budget. There are 31 components in four families:
  - counting, C1–C9;
  - queue and stack operations, Q1–Q7;
  - graph traversal, G1–G9;
  - tree folds, T1–T7 (T7 is a list walk, the unary case).

  Each component states its inputs, effects, aliasing, numeric domain, guards and expansion.

**Expansion.** A component code is followed by one operand per distinct hole, in first-use
order.
- An `id` operand is exactly one literal selection that must be identifier-shaped.
- `pure`, `expr` and `stmts` operands are a code sequence (literals and nested components)
  closed by END.
- The decoder writes the template's fixed text and each operand's decoded bytes in place. A
  hole named twice repeats the same bytes.
- Expansion is byte-exact. There is no whitespace insertion, renaming, hidden helper or
  default operand.
- Nesting is limited to depth 8, and each code consumes at least one field, so decoding
  terminates.

The decoded program must equal a qualified source byte for byte (SHA-256).

**Matching.** A match is admitted only on the acorn 8.15.0 AST (pinned copy, `preserveParens`):
- `id` holes cover exactly one Identifier.
- `expr` and `pure` holes cover exactly one expression node.
- `stmts` holes cover a contiguous run of zero or more statements of one block.
- The fixed text must match the source bytes exactly, and each component's guards must pass
  (Map and Set bindings for C1–C5 and G4, purity for duplicated holes, no reassignment of P
  inside T7's body).

**Audit (Amendment 1).** Cross-problem reuse is necessary but does not exclude a disguised
whole solution. Before freezing, every component is audited for:
- each parameter;
- each callback;
- each constant table, such as the direction lists in G5 and G6 and the 26 in C9;
- each helper;
- each dispatch rule.

Each must be general, stated in the contract and charged in full: constants are fixed text
stored in the dictionary, and callbacks and helpers are program text charged as selections.
A component is rejected if its expansion or guards depend on a problem ID, select behavior by
problem identity, or carry a source payload that is not charged.

A match that fails a guard is rejected and counted. Guards are name-level, not scope-resolved;
that limit is disclosed. Because decoding is byte-exact to a qualified source, the contracts
type the vocabulary and constrain later use, but they do not replace qualification.

**Charging.** Every code is one w-bit selection: literal, component and END codes alike.
- An operand is charged for its own codes (identifiers, constants, sub-expressions, nested
  components) plus END where its type needs one.
- Wrappers (function headers, `solve`, constructor lines) and dependencies (helpers,
  declarations a guard requires) are ordinary program text, so they are charged as selections
  where they occur. No component carries a hidden dependency.
- Dictionary bytes store each template with hole bytes and type tags.
- Package bytes = dictionary + packets (41 framing bytes plus ceil(w x codes / 8) per program)
  + the typed decoder's source bytes. The decoder bytes are reported separately and also
  included in the total.

**Exact parsing.** The parse is the minimum number of codes over literal edges and admitted
component instances, recursing into hole spans (memoized by span). Within the admitted
matches it is exact. It is not a semantic optimum: other equivalent sources are not
considered.

## Arms

There are 24 arms. Each is one source pool (O, Om or R) times one representation (L or T), at
both widths (128 entries / 7 bits and 256 / 8), under one of two fits:
- **F500:** fitted on all 500 and reported on all 500. These are the M1 metrics.
- **Fdev:** fitted on dev-fit 300 and measured unchanged on dev-val 100. This is the component
  comparison. The final held-out 100 is measured once, after the freeze.

The search is the same for every arm:
- Start from the fallback alphabet; T arms also start with END and every component.
- Greedy refill (shortlist 24), then matched80-v3 exact local search with the style150-v2
  chosen-source hybrid proposer (3/4 spans, 1/4 designed forms).
- Designed forms are the STYLE.md forms in L and in T. T's candidate pool also contains every
  component, so search may delete a component and re-add it.
- Proposed spans never cross a component boundary.
- Budget: 60,000 trials per arm; safety limit 6 h per arm; `PYTHONHASHSEED=0`; no ILS (in
  scale500 it added under 1%).

Matched factors:
- Source-only effect: O vs Om vs R under L.
- Dictionary-only effect: L vs T on each pool.
- Combination: T on R against L on O.

## Metrics (M1 thresholds unchanged)

Reported per arm, on all 500 and per cohort, plus dev-val 100 for Fdev:
- selections (all codes), median, p95, worst;
- the fraction of selections that are single-character literal codes;
- END and component code fractions, reported separately;
- programs within 32 and within 96 selections;
- package bytes with and without the decoder;
- whole-program and near-whole entries.

A template counts as near-whole if its fixed text is at least half of a program it matches.

Per component: problems matched, guard rejections, instances used in the final parse, and
selections saved against the matched L arm. Every packet is decoded by an independent JS
decoder, written separately from the Python encoder, to the qualified source hash. One failed
decode fails the experiment, as a wrong acceptance would.

## Predictions

- **D1:** at 256, T-R uses fewer selections than L-R on all 500, but less than 5% fewer. The
  shared style already makes these idioms fixed literal text.
- **D2:** at 256, T's relative reduction over L is larger on Om than on R. Structure partly
  substitutes for naming style.
- **D3:** at 256, L-Om uses fewer selections than L-O, and L-R uses at least 20% fewer than
  L-Om. Style matters beyond compaction.
- **D4:** on dev-val 100 at 256 (Fdev), T-R uses no more selections than L-R. The same holds on
  the final held-out 100 in its single post-freeze measurement.
- **D5:** no arm meets M1.
- **D6:** every packet in every arm decodes byte-exact; zero failures.
- **D7:** the final T-R-256 (F500) dictionary keeps and uses components from at least 3 of the
  4 families.

## Order of work (after the control)

1. Implement:
   - the pinned acorn copy and component matcher, plus guards;
   - the typed evaluator (exact span-memoized parse) and the proposer guard;
   - the independent JS decoder;
   - Om generation and qualification;
   - unit tests on synthetic programs: roundtrip, guard rejections, END and repeat charging,
     and nesting limits.
2. Smoke-test the plumbing with a 200-trial cap; discard the outputs, as earlier freezes did.
   Pin code hashes, Om qualification and the match tables in `contract.json` and commit.
3. Run all 24 arms on Jupiter, verify every packet, then write the README and public evidence
   (aggregates, counts, hashes only).

## Not in this experiment

- **Learned scorer:** only after stronger conventional search shows real headroom. scale500's
  under-1% ILS gain is an observed result, not an upper bound on what better search could
  find. Headroom must first be shown by stronger conventional search finding materially
  cheaper admissible solutions, or by showing that substantial search effort could be
  eliminated. A scorer would then rank already-enumerated candidate moves by predicted
  exact-cost improvement, against that baseline with identical pools, budgets and checks,
  charging training and inference. Training needs the owner's explicit approval.
- **No bit/hex model and no 400-step run.**
- **Not an assembly result:** this is offline vocabulary optimization on known sources. It
  says nothing about M2 or M3 (query-time description-to-program assembly, which keeps its
  non-autoregressive rule).
- **No BITS profile:** a typed representation would need its own slot and decoder under
  [BITS_PROMOTION.md](../BITS_PROMOTION.md).

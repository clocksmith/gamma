# Exact idiom development pilot

`idiom_pilot.py` reuses this directory's joint source/dictionary evaluator. It
compares assistant-authored concrete strings, exact AST expression spans, their
union, and a separate arbitrary-substring compression control. Every candidate
must occur in two distinct problems; multiple variants do not count as reuse.
Multi-character whitespace-only entries and whole source programs are rejected.
Single-character whitespace remains charged and is reported separately.

The evaluator's historical default still includes its 96-entry alphabet.
Explicit `alphabet=[]` enables charged 4–8-bit experiments without that floor.
Unrepresentable text never skips a gap: its longest reachable prefix and minimum
path are retained, and the entire remaining suffix is uncovered. Only complete
sources count toward coverage, selections or percentiles. Equal-cost paths use
lower dictionary IDs; source ties use UTF-8 byte length and the legacy variant
name. Cache reuse binds source bytes and shared literal order.

The pilot reads only the pinned, already exposed scale80 canonical/compact
sources. Their historical evidence is finite development oracle checking plus
original output/input-effect parity. It is not a new catalogue receipt. No
source is rewritten or executed. The legacy manifest lacks the semantics
records needed by `algsolve/authoring_variants.py`; reconciliation stays an
explicit blocker and no competing variant IDs are invented.

```sh
python3 projects/algorithm_solver/literals/joint-v1/idiom_pilot.py \
  --node /absolute/pinned/node --node-sha256 EXPECTED_SHA256 \
  --output /absolute/private/new-run
```

The explicit Node runtime parses text with its bundled Acorn; it never runs a
candidate. Outputs retain the input/code pins, candidate pools, source hashes,
minimum paths, rejected/accepted dictionary moves, coverage, p50/p95, absolute
singleton bits, literal bits, whitespace usage, dictionary/packet storage and
selected decoder source file sizes (not the complete installed runtime
footprint). Source operands, helpers, names and constants remain in the
charged literal text. No editor-control or human interaction cost is claimed.

All four pools share each width's entry budget and search bounds. Actual entry
counts can be lower; padding is not used to dilute singleton share. Comparisons
show per-problem changes against the seed arm and a coverage/bits/singleton/storage
Pareto set. These diagnostics do not assign a readability score or establish
human fluency. A restricted unsuccessful search is not universal infeasibility.

All 80 problems were exposed before this pilot. Repeated runs cannot supply
independent confirmation. Family metadata, modern authoring-variant joins,
larger permitted corpora, independent frozen nonreserved evaluation and browser
admission remain separate work. No pilot result changes the original compact
population, coverage, median 32, p95 96 or 10% singleton-bit gates.
`pilot_numeric_thresholds_met` describes this supplied development population
only; `original_population_gate_evaluated` and `milestone_qualified` remain false.

Focused checks:

```sh
python3 -m unittest discover -s projects/algorithm_solver/literals/joint-v1 -v
```

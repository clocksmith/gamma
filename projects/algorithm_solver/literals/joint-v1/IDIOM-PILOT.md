# Exact idiom development pilot

`idiom_pilot.py` reuses this directory's joint source/dictionary evaluator. It
compares assistant-authored concrete strings, exact AST and syntax-context spans, their
union, and a separate arbitrary-substring compression control. Every candidate
must occur in two distinct problems; multiple variants do not count as reuse.
Multi-character whitespace-only entries and whole source programs are rejected.
The strict arm permits no single-character entries. The fallback arm permits
only charged punctuation, operators and whitespace; never letters or digits.
Neither arm preallocates an alphabet. Complete complementary source-path bundles
seed the dictionary before remaining ranked candidates. The strict seed also
competes as an incumbent in the fallback arm.

Human-oriented paths may split only at parser-derived lexical boundaries,
including Unicode code-point offsets. A whole identifier in one source cannot
silently become a partial identifier or numeric constant in another. Exact
AST leaf/syntax contexts, statement spans, block separators and their whitespace
are proposals, not human-reviewed usability evidence. The compression control
does not enforce lexical boundaries and remains labeled compression only.

The evaluator's historical default still includes its 96-entry alphabet.
Explicit `alphabet=[]` enables charged 4–8-bit experiments without that floor.
Unrepresentable text never skips a gap: its longest reachable prefix and minimum
path are retained, and the entire remaining suffix is uncovered. Only complete
sources count toward coverage, selections or percentiles. Equal-cost paths use
lower dictionary IDs. The compact objective first prefers dictionaries meeting
the aggregate singleton/median/p95 constraints, then compliant program counts,
coverage, reachable prefixes, selections and storage. Joint source selection
prefers compliant alternatives, then minimum selections, UTF-8 size and variant
name. Each alternative still uses its genuine minimum path. No padding or removal
of failing programs can improve a reported percentage. Cache reuse binds source
bytes, lexical boundaries and shared literal order. Prefix progress guides an
incomplete search; it never counts as a represented program.

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

The [retained development comparisons](idiom-results-20261027.json) include all
five attempts, including failures. In the final combined seed/AST strict arm,
64/128/256 entries cover only 3/6/6 of the 80 problems. Their covered-subset
median selections are 22/30/30 and p95 values 31/32/32, with zero singleton
selections. These are **not satisfactory coverage or compact-library passes**.
The fallback arm retains the feasible strict incumbent instead of trading it
for a higher-coverage dictionary above the singleton cap. No BITS vocabulary
was published from these runs. Broader admission and qualified source rewriting
remain required; this control does not substitute for either.

Focused checks:

```sh
python3 -m unittest discover -s projects/algorithm_solver/literals/joint-v1 -v
```

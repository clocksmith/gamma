# Direct BITS development evaluation and finite composition v1

BITS programs can be evaluated directly against independently specified problem
oracles. A native Python/JavaScript source judge is not a prerequisite for this
evidence. This lane executes the existing bounded semantic interpreter, never
arbitrary candidate source, and does not modify or bypass the native judge.

The new result is **automatic example-conditioned composition**, rather than
replaying only hand-selected final graphs: one generic enumerator selects
primitive programs for 24 development specifications, then independently tests
them. Two unsupported specifications remain abstentions.

## Contract and authority

This is additive, repository-owned synthetic software/development evidence under
the [Algorithm Solver charter](../../CATSCAN.md), not a qualification campaign.
The existing catalogue/native judge acceptance, protected-family reservation,
autonomous graph-development/training-loop gate and M1–M6 thresholds remain
unchanged. No corpus source, protected case or existing benchmark population is
read. No historical receipt is reclassified.

The following are separate and explicit:

- 26 authored development specifications, not 26 catalogue problems.
- The 24 supported tasks share one list-processing grammar. They are not 24
  independent algorithm families or evidence of broad unseen-problem solving.
- Search receives ordered input/output examples, not natural-language statements,
  task names, expected solution graphs, oracle callbacks or evaluation cases.
- Human-authored generic combinators and scalar grammar define the search space.
  Search discovers combinations and parameters within it; it does not invent the
  heap-sort algorithm or a new primitive language from scratch.
- Independent test inputs are disjoint from search examples, but the task suite
  and grammar were developed together. This is **development testing**, not an
  untouched, family-disjoint holdout or proof of correctness.

No goal completion, native JavaScript/Python qualification, human fluency,
publication result, 1,000-problem coverage or superiority to ordinary code is
claimed. Component authority and intent are preserved.

## Implementation

- [direct_bits_search.py](../../algsolve/synth/direct_bits_search.py) enumerates
  plans, lowers them into primitive graphs, selects the first training match,
  serializes charged packets, and evaluates decoded packets.
- [direct_bits_oracles.py](../../algsolve/synth/direct_bits_oracles.py) specifies
  domains and expected behavior using independent Python mathematical/library
  operations. It imports no candidate code, interpreter or corpus.
- [measure.py](measure.py) separates frozen selection from independent scoring.
- [Focused tests](../../tests/test_direct_bits_search.py),
  [oracle checks](../../tests/test_direct_bits_oracles.py) and
  [adversarial checks](../../tests/test_direct_bits_adversarial.py) cover the
  changed behavior.

The unchanged 57-entry `vector-v1` dictionary supplies all computation. Generic
map/filter/scan/sort/distinct stages are **search notation**, not new uncharged
packet opcodes. Every stage expands into loops, branches, bindings, arithmetic,
heap/map/vector operations, and all their operands. There is no answer lookup,
recipe dispatch or native source hole in the selected packet.

The frozen grammar has 34 stages, zero through two ordered stages, and four
terminals: list result, sum, product or length. Scalar expressions come from
`x`, 0, 1, unary negation and one binary add/subtract/multiply layer, plus one
explicit conditional form for negative values. All 4,764 plans are considered
in the same deterministic order for every task. No task-specific selection path
exists. The first exact match to 18 training examples is retained; later test
failures cannot trigger another candidate or a repair.

Selection writes `selection.json` and a full `trace.jsonl` before evaluation cases
are generated. The trace retains every candidate's plan, graph and behavior
hashes, failure and match outcome. Scoring verifies source, grammar, trace,
packet, graph, plan, cost and training bindings before independent tests. A
source change invalidates the selection instead of silently reusing it.
Existing differing outputs are not overwritten: use a new output directory.
Hashes supply reproducibility bindings, not cryptographic attestation of an
untrusted report author. Fresh replay supplies independent verification.

Each packet is checked and decoded once per evaluation set. The validated graph
then uses the unchanged bounded interpreter with fresh owned resources, copied
inputs and a new operation budget per case. Expected outputs remain only in the
host comparator. Execution exceptions fail the case, retain evidence and do not
skip later cases. Integer and boolean answers are distinct. Failed executions
are charged: consumed work is capped at the budget and attempted charges are
reported separately when a primitive's charge exhausts it.

## Independent specifications and domains

Supported tasks are sum, positive/nonzero counts, positive-square/square/absolute/
negative/incremented sums, product, positive/negative/nonzero filters, square/
negate/absolute/double/increment maps, prefix sums, ascending/descending sorting,
stable distinct, sorted distinct, stable distinct absolute values and stable
distinct squares. Reverse-input and adjacent-differences tasks are explicit
negative controls outside this frozen grammar.

Each task has 18 training inputs and 971 disjoint evaluation inputs:

- 769 exhaustive-small cases, completing all lists of lengths 0–4 over
  `{-2,-1,0,1,2}` together with the training examples.
- 10 domain-boundary cases.
- 192 reproducibly seeded varied cases.

General inputs have length at most 32 and integers in [-1,000,000, 1,000,000].
Product uses length at most 16 and [-8,8], keeping every accepted intermediate
inside the runtime's 128-bit magnitude limit. The per-case limit is 100,000
declared operation units. These finite tests do not qualify larger inputs,
all 128-bit inputs or asymptotic complexity. Input preservation and fresh-state
behavior have separate regression checks.

## Measured result

Frozen evidence is in [evidence/selection.json](evidence/selection.json),
[evidence/trace.jsonl](evidence/trace.jsonl) and
[evidence/evaluation.json](evidence/evaluation.json).

- 24 of 26 specifications selected and independently passed.
- 2 of 26 abstained after the full search, as intended for the negative controls.
- No selected program failed independent evaluation.
- 23,304 distinct task/input evaluations; the same tests at 6/7/8 bits give
  **69,912 passing executions**. Widths do not multiply the number of problems.
- Search: 4,764 candidates, 85,752 training executions, 5,320,950 operation units.
- Evaluation: 6,519,240 operation units across all widths.
- One observed run took 3.187 seconds for search and 3.477 seconds for scoring
  on this executor. These are measurements, not a performance comparison or SLA.

Four selected programs use two ordered stages, including positive-square sum,
sorted distinct, stable distinct absolute values and stable distinct squares.
Others combine one stage with a reduction or directly reduce the input. The
chosen squared-value map uses multiplication, while doubling uses addition:
the final graph need not reproduce an authored solution's source.

## Complete representation costs

All 24 selected programs occupy 4,510 bytes at six bits, 4,834 at seven bits, or
5,146 at eight bits, including every packet's 107-byte frame and padding.
Six-bit packets range from 142 to 286 bytes.

Each alternative executable package additionally pays 35,852 shared source bytes:
911 dictionary bytes, 15,401 decoder bytes, 19,378 owned-vector runtime bytes,
and 162 package-initializer bytes. Totals are therefore 40,362 / 40,686 / 40,998
bytes for 6/7/8 bits. These packages use `typed_word_codec.execute`; they do not
require the search, oracle or measurement code to run a selected program.

Composer, oracle and measurement source bytes are separately reported, as is the
1,447,070-byte rejected-attempt trace. They are research-tooling costs rather than
hidden runtime requirements. Python/standard-library binaries are explicit
external environment dependencies, not included deployment bytes. No human
interaction time, editing effort, encoder keystrokes, search optimality or
compression advantage against ordinary source is established. Seven/eight bits
have no richer primitive dictionary in this version.

## Reproduce and verify

From the repository root:

```sh
PYTHONPATH=projects/algorithm_solver python3 -m unittest discover \
  -s projects/algorithm_solver/tests -p 'test_direct_bits_*.py' -v
python3 projects/algorithm_solver/literals/direct-bits-development-v1/measure.py \
  select --output /tmp/direct-bits-replay
python3 projects/algorithm_solver/literals/direct-bits-development-v1/measure.py \
  score --output /tmp/direct-bits-replay
diff -r projects/algorithm_solver/literals/direct-bits-development-v1/evidence \
  /tmp/direct-bits-replay
```

The three evidence files are deterministic. Wall-time measurements are printed
separately and excluded from replay equality. Reproduction uses only the Python
standard library and existing bounded interpreter. It needs no native sandbox,
model, network, installation or source-generation service.

Local verification: 20 direct-lane tests and 37 existing typed codec, owned-vector
and base-runtime focused checks passed (57 total). Python syntax checks passed;
all three evidence files matched a fresh replay byte for byte. Full repository, native judge,
catalogue and release qualification were not run or claimed. The prior native
judge environment problem is unrelated to these direct-interpreter results.

## Remaining concrete work

The next language expansion needs genuinely new domain support, such as indexed
sequences, text/Unicode, richer tree/graph shapes and their independent bounded
contracts. The next composition result needs a prospectively frozen procedure
and authorized family-disjoint tasks, rather than counting related development
specifications as new problems. Broader source catalogue qualification and human
binary-input studies remain their separate goals. No existing protected split is
opened by this implementation.

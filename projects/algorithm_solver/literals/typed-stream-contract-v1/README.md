# Typed prediction to charged stream contract v1

This additive bridge reconciles the existing encodings without changing their
frozen codecs, runtime semantics, training vocabulary or qualification scope.
Implementation: [`typed_stream_contract.py`](../../algsolve/synth/typed_stream_contract.py).

## The 43/53/57 distinction

- The predictor has **43 node labels**: 11 tree/statement/reference/literal labels,
  14 pure operations, 14 effects and 4 recipe labels. `EMPTY` is padding, not an
  executable semantic operation. Labels alone omit edges, bindings, constants,
  fitted types and externally supplied parameter names/count.
- The matching **base-v2 word profile has 53 entries**: 16 grammar/numeric words,
  14 pure operations, 14 effects, 7 atomic types and 2 type constructors.
- The **vector-v1 word profile has 57 entries**. It adds `E:vector.new`,
  `E:vector.append`, `E:vector.snapshot` and `T:vector_int`, under a distinct
  runtime schema. These operations are not in the frozen predictor.

`descriptor()` supplies the actual numeric code mappings for all 43 labels and
both full word vocabularies. Numeric IDs cannot be copied between the encodings.
Even common type words have different IDs across word profiles because vector
operations precede types. A label mapping is not itself a semantics-preserving
conversion of whole programs.

## Exact conversion and incompatibilities

`from_prediction(codec, codes, params, width=6)` first uses the existing predictor
validator. It then expands the pinned **base** recipe catalogue hygienically and
encodes the resulting primitive graph with the existing base-v2 word codec.
It returns packet bytes and an inspectable, hash-bound cost report. Decode remains
subject to all existing type, ownership, graph-budget and lexical-scope checks.
The input code tensor is not mutated or trained here.

| Prediction field | Charged stream representation |
| --- | --- |
| `root`, `sequence` | `PROGRAM`, `BLOCK`, explicit counts, ordered signature and return |
| first-child/next-sibling edges | Prefix grammar, explicit block/argument/tuple counts; no external edge table |
| `let`, `var`, `set` | `LET`, `VAR`, `SET`, explicit binding index and value |
| `for`, `if` | `FOR`, `IF`, explicit iterable/condition and child blocks |
| `pure:*`, `call:*` | `P:*`, `E:*`, charged arity, arguments and effect output binding |
| Input/declaration references | `REF` plus numeric sequential binding index |
| Integer sign + 128 LSB-first magnitude bits | `INT`, `POS/NEG`, canonical MSB-first `BIT0/BIT1`, `END` |
| Boolean bit fields | One `TRUE` or `FALSE` word; never integer coercion |
| Fitted type IDs | Explicit `T:*` words and compound type arities |
| Four `recipe:*` labels | Full base primitive expansion, including every repeated body and introduced binding |
| `EMPTY` slots | No word; predictor capacity remains separately reported |

Input references `0..7` and declaration references `8 + declaration_slot` become
explicit sequential `bN` identities. These are not the same integers. For example,
with one input, a `let` in prediction slot 2 has reference ID 10 but becomes word
binding `b1`, encoded `BIT1 END`; references add `REF`. The original input is
`b0`, encoded `BIT0 END`. Expansion can insert further declarations, so recipe
references require full scope-aware conversion, not a flat numeric substitution.

Original cosmetic names and recipe boundaries are not preserved. Raw tensor,
parameter-order, predictor-descriptor and recipe-catalog hashes are retained in
the bridge report; the resulting packet carries the existing dictionary/runtime/
decoder identities. Ignored prediction fields are not an additional information
channel. This is **not lossless prediction-tensor transport**.

`to_prediction(packet, codec)` supports base-v2 primitive graphs only and checks
an exact canonical graph roundtrip. Expanded recipes are not refolded. A valid
packet can exceed the fitted prediction slot budget, its eight-input limit or
its fitted type vocabulary. Those conversions fail instead of changing the graph.
All vector-v1 packets are rejected, even if a particular packet uses only common
operations. No vector schema is relabeled as base-v2. Replacing immutable
`append` with owned vector mutation would be a separately validated algorithm
change, not an encoding reconciliation. Existing recipes are not swapped for
vector recipes.

## Complete cost partition

`ledger(packet)` validates the actual packet and partitions every payload word:

- **Operations:** `LET/VAR/SET`, pure and effect opcodes.
- **Bindings:** declaration/output/set/loop/input indices and all `REF` words and
  reference indices. Every index digit and terminator is charged.
- **Structure:** `PROGRAM/BLOCK/FOR/IF`, parameter/statement/argument counts,
  including every count digit and terminator.
- **Constants:** Boolean words and the full integer tag/sign/magnitude/terminator.
- **Types:** atom/constructor words and tuple arities, including their numerals.

The same numeric words are classified by grammatical context. Categories are
nonoverlapping and sum exactly to `selections * width`. The trace gives the word,
code, position and category for every selection and is checked against the actual
validated packet. Framing is another 856 bits; minimal byte padding is additional.
The original codec's exact packet and dictionary/decoder/runtime source-storage
costs are retained. Shared support is charged once per package, not per program.
Conversion-tooling source hashes/sizes are separately reported and overlap with
packet support, so the two source inventories must not be blindly summed.

The predictor report counts allocated fields, including padding, and active nodes.
Its `wire_bits` is null because it has no defined packed transport here. Six bits
per node label is not a complete stream cost. The packet includes all typed
program data needed by its decoder, but not model storage, Python/interpreter
binaries, compilation/search time, human navigation/corrections or runtime inputs.
Unmeasured human interaction is not assigned zero cost.

## Authored evidence and replay

[`synthetic-evidence.json`](synthetic-evidence.json) contains packets, complete cost
partitions, concrete mapping, source hashes and five authored examples at widths
6/7/8. Codes are exact encodings of supplied graphs, **not learned predictions**.
These checks do not open a corpus or protected population, qualify native sources,
measure autonomous correctness, or promote a vocabulary.

From the repository root:

```sh
PYTHONPATH=projects/algorithm_solver python3 -m unittest discover -s projects/algorithm_solver/tests -p test_typed_stream_contract.py -v
python3 projects/algorithm_solver/literals/typed-stream-contract-v1/measure.py > projects/algorithm_solver/literals/typed-stream-contract-v1/synthetic-evidence.json
```

Tests cover the full label mapping, exact context-sensitive cost partition,
input order, lexical branch bindings/mutable cells, all existing recipe fixtures,
repeated expansion, signed 128-bit bounds, Boolean identity, reverse slot/type
rejection, vector snapshots/profile refusal and malformed streams/trees.

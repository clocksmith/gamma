# Previous completed word: one literal prediction mutation

Owner: `root_explore`, with `next_prediction_gate_review` implementing the
synthetic adapter. This is implementation development, not a corpus launch.
The parent remains the immutable `opcode_field_compact_v1` packed source,
SHA256 `7d331ba82c635af8afe6517bf5f4471b41dcf7854c6ec01cb5564078d9bb56a8`.

The parent discards a completed ASCII word at its delimiter. The hypothesis is
that retaining that word's final eight bytes improves prediction of the next
word after intervening bytes have displaced it from the existing contexts.
This is bounded causal history, not semantic parsing or a pretrained dictionary.

The [calibration receipt](../operations/provenance/opcode_calibration_terminal_20260908.json)
measures 476,715.553744 ideal bits of coded-literal loss. That is a measured cost,
not attainable savings. The event-only opportunity diagnostic supplies a smaller
fixed opportunity budget; neither result proves a full-corpus compression bound.
The failed field-body history and literal-only SSE policies remain distinct:
this mutation changes neither field history routing nor the SSE training law.

## Fixed mechanism and controls

Maintain the last two completed ASCII-word suffixes, eight bytes each. A word
completes only when a non-letter follows a nonempty current word. Repeated
delimiters do not shift history again. Preserve case and the existing modeled
byte coordinates, including opcode escapes. Update on every reconstructed byte,
including bytes emitted by overlapping copies.

| Arm | Context family 11 | Extra history |
| --- | --- | --- |
| P | Original `(prefix, column >> 3, field)` | None |
| K | Original | Both completed words |
| D | `(prefix, previous suffix8, current suffix2, field)` | Both completed words |
| S | `(prefix, delayed suffix8, current suffix2, field)` | Both completed words |

S uses the second previous completed word; it is a causal delay control.
Keep the other eleven context families, twelve-table count, mixer, calibration,
count rescaling, tokenizer, frontend, copy finder and arithmetic coder unchanged.
Freeze the original `lit_prefix` namespace before replacing either state or
literal predictor classes. This preserves the parent's copy-cost estimates.
Verify the actual copy/event decisions rather than infer equality from code.

The decoder learns each history value from bytes it has reconstructed. Before
each prediction, both sides have the same completed histories and current word.
Identical integer prediction and update laws therefore preserve synchronization
by induction. Exact inverses and state witnesses test the implementation; this
argument does not establish any size improvement.

## Bounded synthetic acceptance

One fixed configuration; no parameter sweep or confirmation data. Each fixture
has at most 4,096 raw bytes. Adapter tests use CPU 3; independent observation
tests use CPU 2. Each suite has a 512MiB address-space ceiling, 120 CPU seconds,
180 elapsed seconds, and at most 32MiB of retained files. No corpus execution,
installation, candidate publication, HORIZON change or MIDAS change is authorized
by this document. Fresh admission is required before a separately frozen gate.

Require independent inverses, fresh encodes and identical repeats for P/K/D/S;
P/K archive and parent-state identity; identical parse witnesses across arms;
and encoder/decoder agreement on probabilities, updates, coder state and both
completed-word histories. Include empty input, arbitrary bytes, malformed markup,
case, long words, repeated delimiters, opcode escapes and overlapping copies.
Include a fixture where the immediate predecessor adds no distinct context.
An intentionally corrupted history witness must fail comparison.

Report actual archive bytes and deterministic local package sizes separately.
Twelve tables do not imply unchanged RAM: different keys can change cardinality.
The sixteen logical history bytes are not a claim about Python object memory.
Runtime distribution, licenses, official package multiplicities and options
remain separate complete-package obligations.

After synthetic acceptance, publish a prospective opening250KB P/K/D/S gate
with source, population, ancestry, guards, package inventory and unique ownership.
Require D to beat P/K and S, then assess delivery cost before fresh confirmation.
Classify inverse/state failure, budget exhaustion and compression loss separately.
Synthetic compression differences earn zero full-corpus credit. The active
objective remains 90,000,000 complete bytes.

The executable adapter is `lib/opcode_previous_word_v1.py`. The deterministic
builder is `tools/opcode_previous_word_build_v1.py`; its `write_bundle(Path)`
creates an independent directory with `p`, `v` and `program.py`, refusing an
existing destination. The synthetic command adapter supports exact encode/decode
with `--candidate-root`, `--arm P|K|D|S` and an optional `--audit` path:

```bash
python3 tools/opcode_previous_word_observe_v1.py encode fixture.raw output.arc \
  --candidate-root results/OWNED_BUNDLE --arm D --audit results/OWNED_AUDIT.json
```

That command enforces the synthetic input size; external CPU/address/elapsed
bounds remain required. It is not a corpus runner. Run the two
`test_opcode_previous_word*.py` suites for adapter and independent observation
checks. The completed synthetic receipt binds the exact source and retained
artifacts; subsequent semantic edits require a new version.

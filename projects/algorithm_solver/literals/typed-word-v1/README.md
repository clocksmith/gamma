# Charged typed semantic words v1

This additive representation serializes Gamma's actual typed primitive IR as
fixed 6-, 7- or 8-bit selections. It is not a source-character keyboard, source
escape, new interpreter, corpus coverage measurement or autonomous solver.
The existing typed program, recipe, target and prediction codecs are unchanged.

Implementation: `algsolve/synth/typed_word_codec.py`.
Tests: `tests/test_typed_word_codec.py` within the algorithm_solver project.

## Operation surface

Two explicitly versioned profiles:

- `base-v2`: `algsolve.typed-program.v2`, 53 dictionary entries.
- `vector-v1`: `algsolve.typed-program.vector.v1`, 57 dictionary entries.

Both fit within 64 entries and use the same semantic operation order at all
three widths. Seven/eight-bit words currently add payload cost without richer
operations; no wider-width advantage is claimed. Wider widths do not gain hidden operations. Unused codewords are
invalid, not escape slots or padding entries.

Statements are `let`, `var`, `set`, `for`, `if` and the explicit effect operations.
Pure operators are add, sub, mul, eq, lt, not, neg, len, range, tuple, field,
empty_ints, append and sort_by. Base effects are DSU new/find/union; heap
new/push/pop; queue new/push/pop/size; map new/has/get/set. The vector profile adds
vector new/append/snapshot and the vector_int resource atom. All original runtime
typing, ownership, mutable-cell and lexical-scope rules apply.

Types include int/bool/unit, named resources, and recursive list/tuple types.
Resource parameters/results, resource aliases, illegal types, unbound references,
forward references and escaped branch locals remain invalid.

## Names, literals and recipes

Input parameter order is preserved as positional ports. All parameters, local
bindings, loop items and resource handles are hygienically renamed to sequential
`b0`, `b1`, etc. Every declaration **and** every reference/set carries its charged
numeric index. Original cosmetic names are not transmitted and are not needed
to decode. Input values are runtime arguments, not embedded solution data.

A natural number is MSB-first BIT0/BIT1 codewords followed by END. Zero is exactly
BIT0 END; leading zeros and empty numerals are invalid. Integers carry INT,
POS/NEG, magnitude words and END. Negative zero is invalid. Every binary digit,
sign and terminator costs the full selected word width. The existing 128-bit
magnitude bound applies. Counts, arities, tuple widths and indices use this same
charged structural representation, with tighter contextual limits.

Booleans have TRUE/FALSE words and remain distinct from integers. Graph literals
cannot carry text, Python source, arbitrary JSON, operator names or unbounded
constants through an escape channel.

Recipe calls are validated and hygienically expanded into primitive graphs before
encoding. Every repeated expansion is paid in full. No recipe identifier, whole
solution table or algorithm-specific recipe opcode appears in the dictionary.
The caller may supply its explicit recipe map; decoding requires no recipe map.

## Wire grammar

The payload is a concatenation of fixed-width dictionary indices:

- PROGRAM, parameter count, each parameter index/type, output type, body block,
  return expression.
- BLOCK, statement count, statements in execution order.
- LET/VAR/SET, binding index, value expression.
- An effect word, output binding index, argument count and argument expressions.
- FOR, item binding index, iterable expression, body block.
- IF, condition, then block, else block.
- REF plus index; INT plus sign/magnitude; TRUE/FALSE; or a pure-operation word
  plus argument count and arguments.
- Atomic type word; list word plus element type; tuple word plus field count/types.

There are no implicit scalar operands or free binding side tables. Fixed grammar
ordering and the standard operation semantics belong to the charged decoder.

The 107-byte big-endian frame contains magic TWIR (4 bytes), version/width/profile
(1 byte each), word count (4 bytes), and SHA-256 identities of dictionary,
selected runtime source and decoder source (32 bytes each). Minimal trailing
zero padding completes the final byte. Length, padding, identities and reserved
codewords are checked before grammar interpretation. Extra words/bytes fail.
Source changes invalidate old packets rather than silently changing semantics.

## Costs and limits

`encode(program, width, profile, recipes=None)` returns packet bytes and costs.
`decode(packet)` validates and reconstructs the canonical primitive graph.
`execute(packet, positional_inputs, budget=100000)` executes that graph through
its pinned runtime with exact ordered input arity, fresh resources and copied
inputs. Budgets must be integers from 1 through 2,000,000. It never evaluates
source and is not a native sandbox qualification route.
`canonicalize(...)` exposes the exact expected graph for independent inspection.
`descriptor(profile)` reports stable mapping and current dependency identities.

Costs separately report payload selections/bits, numerical/control selections,
per-word counts, framing, padding and exact packet bits. Dictionary JSON bytes,
decoder implementation source bytes and selected IR runtime source bytes are
charged separately. The one-program-with-support total sums all four storage
categories. For multiple programs, count shared support once, not once per
packet. Report packet costs and support costs separately rather than hiding
amortization. Python interpreter and standard-library binaries are explicitly
external environment dependencies; their deployment size is not measured here.
Encoding/search/recipe expansion time and human interaction costs are not measured.

Decoding is capped at 262,144 words and 48 recursive grammar levels; constructed
nodes/counts/indices are bounded by the IR's 4,096-node limit. The IR then applies
its complete JSON-tree/type/scope validation. Bytes must be canonically encoded;
structural re-encoding must reproduce the same words. Decode does not execute
an input graph.

## Evidence

Run from the repository root:

`PYTHONPATH=projects/algorithm_solver python3 -m unittest discover -s projects/algorithm_solver/tests -p test_typed_word_codec.py -v`

Authored fixtures exercise mutable loops/branches, resource operations, compound
types, signed 128-bit values, booleans, alpha-renaming, recipe expansion and owned
vector snapshots. They compare direct and decoded execution against explicit
expected results at every width. Malformed framing, stale identities, unused
words, padding, trailing data, noncanonical numerals, invalid references/types,
decode nesting/count bounds, positional arity, execution budget failure and
fresh ownership across repeated packet runs are tested.

These are finite synthetic development checks. No private source/cases are read,
no new native source receipts are created, and no claim is made about qualified
catalogue coverage, independent problem solving, human fluency or M1–M6 completion.

## Authored fixture cost receipt

`synthetic-evidence.json` is rebuilt by `measure.py` using four source-independent,
explicitly authored typed graphs. Reproduce with:

`python3 projects/algorithm_solver/literals/typed-word-v1/measure.py`

| Authored graph | Selections | 6-bit packet | 7-bit packet | 8-bit packet |
|---|---:|---:|---:|---:|
| Signed constant -257 | 19 | 976 bits | 992 bits | 1008 bits |
| Mutable sum loop | 46 | 1136 bits | 1184 bits | 1224 bits |
| Map with stored-zero/default distinction | 60 | 1216 bits | 1280 bits | 1336 bits |
| Owned vector with independent snapshots | 85 | 1368 bits | 1456 bits | 1536 bits |

Each packet includes the 856-bit frame and minimal byte padding. Support source
and dictionary storage is additional and explicitly recorded in the receipt.
Per-profile packages sum packet bits and charge that profile's dictionary,
decoder and runtime once. Combined-profile packages charge the common decoder
once and each dictionary/runtime once. Neither total multiplies support storage
by program count or width. Python/environment dependencies remain excluded as
stated above. The measurement helper and test fixtures are research tooling, not
required decoder dependencies.

The receipt pins exact current descriptor/runtime/decoder/measurement hashes and
records direct-versus-decoded authored expected-result checks. These four graphs
are not four newly qualified corpus solutions. No protected, unseen, training or
catalogue populations were opened. Larger word widths have no richer dictionary
in this version and increase packet size; no width-win claim is made.

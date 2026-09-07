# Fixed-grammar execution-conditioned coding

This development experiment tests prediction from decoder-known execution
state. It preserves the selected D2GRAM01 graph, including its repeated argument
references. It does not select new rules or alter argument bindings.
The earlier exact enumerative evaluator remains available and unchanged.

Ownership and the comparison are recorded in
[the prospective plan](../operations/provenance/dualstream_event_v1_plan.json).
Use the existing adaptive queue and
[runner](../tools/dualstream_event_gate_v1.py) for the corpus gate; direct CLI
commands below describe synthetic use, not an alternative admission route.

## Comparison

| Arm | Input representation | Storage/prediction |
| --- | --- | --- |
| P | Retained raw-byte baseline | Original Deflate archive, exact diagonal |
| B | Retained selected grammar | Original Deflate archive, exact diagonal |
| R | Original raw bytes | New adaptive integer context coder |
| G | Same selected graph as B | Typed events and sequential context |
| X | Same graph and event schedule as G | Adds interpreter context |

X must beat G, R and P before a fresh confirmation population is considered.
A passing implementation or smaller grammar dictionary alone grants no such
transition. Every comparison uses the original independent raw frame partition.

## Format and interpreter

`D2EVENT1` has a 25-byte header: magic, arm identifier, frame capacity, frame
count and raw length. Each frame has a 73-byte header carrying raw length,
original grammar mode, payload length, raw SHA256 and graph SHA256.
The payload is one arithmetic event channel with explicit termination,
lookahead and a 32-byte complete-state checksum.

Phrase definitions, template definitions and structure-rule definitions are
decoded before their root uses. Each reference uses an alphabet bounded by
already decoded definitions; forward and cyclic references are invalid.
Literal nodes are interned at their first transmitted occurrence. The first
occurrence sends an exact length and spelling bytes; later occurrences send
the literal identifier. This transmits the existing graph, without discovering
an additional grammar.

Root instructions are decoded and executed in order. A content reference is
decoded when execution needs its next literal; a phrase expansion may remain
pending across intervening structure instructions. A template argument is
decoded at its first use, stored at its declared argument index, and reused
exactly at subsequent uses. First-use order need not equal argument-index order.
Empty arguments remain valid. Supplied arguments are retained in the original
graph's index order. Literal, phrase and repeated-argument expansion updates
output history for every emitted byte.

The decoder does not parse or normalize XML. Spelling, whitespace, entities,
malformed markup and arbitrary bytes are preserved by the emitted program.

## Probability model and state

The exact model specification is exported as `MODEL_SPEC` by
[the kernel](../tools/dualstream_event_coder_v1.py) and bound by the run plan.
An event is an integer in its declared alphabet, coded through a balanced
binary decision tree. It is not a collection of opaque varint bytes.
All arms use 32-bit arithmetic intervals and nonzero Q16 probabilities.

There are 4,096 backing count cells and 65,536 specific count cells. Both use
deterministic tagged replacement. Specific counts interpolate with the backing
distribution with strength eight. Counts update after each decoded bit and
rescale at total 32,768. Unseen backing contexts use counts `(1,1)`; every
symbol has nonzero support, so no explicit escape token is needed.

Common context contains event type, alphabet/tree prefix, the two preceding
event identities and the last four reconstructed bytes. X additionally uses
the declared execution phase, template identifier, instruction position and
argument index. The predictive difference is confined to this additional key.
G still executes the same interpreter and maintains the same evidence.

Both sides start from the same empty state. Given equal state, they compute
the same probability, decode the same next event, and execute the same update.
Backward references terminate; expansion emits the exact bytes bound by the
decoded definitions. Induction proves synchronization and inversion under
these procedures. It supplies no compression-ratio guarantee.

The kernel records every probability, count replacement/update, common coder
state and emitted byte in rolling hashes. The decoder independently maintains
a canonical encoder shadow; it rejects a mismatching payload or state checksum.
Interpreter boundary chains bind definition/binding prefixes, output, work
counters and pending-expansion cursors after definitions and each root.
Complete graph and model hashes are compared at frame closure. Evidence
distinguishes decoder-only lookahead from common arithmetic state.

## Costs and limits

Reports contain additive actual archive bytes. Literal spelling lengths and
bytes are `definitions`; grammar definitions, instructions and calls are
`program`; executed content references and R's bytes are `content`; first-use
argument bytes are `arguments`. Whole arithmetic bytes are attributed to the
category being processed when the coder emits them. This is an accounting
convention, not an independent compressed section size. Deferred termination,
checksums and file/frame headers are `framing`.

Each raw frame is at most 65,536 bytes; the interface caps total raw input at
1,000,000 bytes. Stored instructions, dictionary bytes, expansion work and
channel events have explicit limits. The run contract additionally fixes CPU,
address space, scratch, file size and elapsed stops using synthetic measurements.
Independent discovery timing remains diagnostic on a shared host.
Source/runtime inventory is reported separately. Complete package and license
qualification remain unresolved; no small archive establishes the 99M target.

```bash
python3 -m unittest -v tests.test_dualstream_event_codec_v1
python3 tools/dualstream_event_codec_v1.py encode synthetic.raw raw.event --mode R
python3 tools/dualstream_event_codec_v1.py encode selected.d2g grammar.event --mode X
python3 tools/dualstream_event_codec_v1.py decode grammar.event restored.raw
```

The structural-context hypothesis has precedent in
[XMLPPM's multiplexed hierarchical modeling](https://xmlppm.sourceforge.net/paper/node6.html).
Its results motivate this controlled test; they are neither Gamma attribution
nor evidence of performance on this population.

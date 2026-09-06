# Standalone two-stream grammar

`tools/dualstream_grammar_v1.py` is a new local implementation of the supplied
algorithm specification. The linked prototype ZIP was unavailable on this host;
its code and reported measurements have not been verified or imported.

The encoder inspects independent frames of at most 65,536 bytes. It preserves
every byte, including invalid UTF-8 and malformed markup. Recognized markup is
an optional literal grouping hint. No XML normalization occurs.

The structure stream holds a shared literal pool, phrase definitions, parameter
templates, and root instructions. The content stream supplies lexical tokens
and length-delimited invocation arguments. Common prefixes and suffixes across
similar records become exact literals; varying spans become arguments. Equal
spans within an invocation are supplied once and reused through argument
references. Templates can use earlier phrase rules. This version does not infer
nested calls between parameter templates.

Phrase rules refer only to earlier rules. Template definitions precede calls.
The decoder validates references, consumes all arguments and lexical tokens,
limits total interpreter work and output length, and checks each frame's SHA256.
It does no grammar discovery or model training. File operations process frames
sequentially and publish new outputs atomically; existing targets are refused.

Five separately Deflated sections make accounting additive: literal definitions;
program definitions and structure instructions; lexical content; supplied
arguments; framing. Template argument opcodes belong to structure bytes.
Exception bytes are zero: unmatched records use exact literal instructions.
Each section's reported compressed size includes its backend tables. Complete
Python/zlib/source distribution accounting is still separate.

The four comparisons share zlib level 9 and identical frame boundaries:

- `plain`: raw frames through Deflate.
- `split`: structure and lexical references with a shared literal pool.
- `grammar`: recursive phrase factoring in both streams.
- `parameter`: parameter templates, repeated argument bindings, and phrase
  factoring across content and template literals; it retains `grammar` when
  the parameter representation does not pay.

The optional `auto` mode also falls back to `plain`. Every proposed change is
selected from its actual complete encoded frame size, not displaced-byte counts.
This is a bounded greedy search, not an optimal-grammar claim. Shared XML grouping
and phrase grammars have prior art; the tested hypothesis is their particular
combination with paid exact argument bindings.

```bash
python3 tools/dualstream_grammar_v1.py encode input.bin output.d2g --mode parameter
python3 tools/dualstream_grammar_v1.py decode output.d2g restored.bin
cmp input.bin restored.bin
python3 -m unittest discover -s tests -p 'test_dualstream_grammar*.py' -v
```

The standalone limit is 1,000,000 raw bytes. Actual corpus comparisons use
`tools/dualstream_grammar_gate_v1.py` through the existing adaptive queue.
Development may compare eight declared configurations; validation selects one
before a separately frozen 1MB confirmation. The worker runs each encode,
decode and repeat in a separate bounded process and retains all outcomes.
Source revisions, populations, controls, budgets and ownership must be published
before release. Pin the canonical launcher to CPU2 before fork. HORIZON and all
model campaigns are independent of this codec.

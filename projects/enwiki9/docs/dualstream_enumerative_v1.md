# Exact enumerative grammar costs

`tools/dualstream_enumerative_v1.py` stores each existing serialized grammar
section as multiset ranks over byte symbols in fixed 4096-byte chunks. It does
not select a new grammar. It preserves the exact graph through the existing
fixed-program adapter; old and tokenized argument formats remain explicit.

For counts c with sum n, M = n! / product(c!) is computed using integer binomial
coefficients. A rank in [0,M) occupies `((M-1).bit_length()+7)//8` bytes. M=1
therefore uses zero rank bytes; M=256 uses one. Fenwick counts implement the
lexicographic interval update and its inverse with integer arithmetic.

The decoder reads sorted positive counts for each bounded chunk, rejects
invalid ranks and lengths, and reconstructs every section. A private copy of
the existing interpreter accepts these raw sections. Token arguments have an
explicit bounded conversion to whole-argument references. Existing modules and
sealed files are unchanged. Grammar expansion retains backward-only references,
argument consumption, output limits and per-frame raw SHA256 checks.

Every actual byte belongs to one category: literal-definition, grammar-program,
structure, content or argument rank bytes; count tables; stream lengths; or
archive/frame headers. Exceptions in these existing representations are literal
bytes; there is no additional exception stream. Raw dictionary lengths are
diagnostics, never charged again after their encoded bytes are counted.

The executable certificate checks the sum against the realized archive length.
Adding a complete counted package C could certify a specific full-corpus size;
neither this conditional statement nor a prefix receipt proves C+archive <=99M.
The package inventory separates encoder adapters, decoder source and unresolved
runtime/license/distribution accounting. Source-archive repeats prove fixed
serialization only, not fresh grammar-discovery determinism.

The frozen comparison uses unchanged plain Deflate P, old grammar Deflate B,
enumerative B sections E, the same B graph with token arguments T, and plain
byte enumeration R. All use identical raw frame boundaries. The old selected
program contains twelve repeated-argument references, preserved by B/E/T.
T tests argument storage; it does not add or remove bindings.

Run synthetic correctness with:

```bash
python3 -B -m unittest discover -s tests -p 'test_dualstream_enumerative*.py' -v
```

The published v3 candidate invokes `tools/dualstream_enumerative_gate_v3.py`
through the existing adaptive queue. The direct codec interface is:

```bash
python3 tools/dualstream_enumerative_v1.py encode selected.d2g archive.d2e --storage old
python3 tools/dualstream_enumerative_v1.py decode archive.d2e restored.raw
```

No dependencies are installed. Definitions, counts and exceptional bytes are
transmitted. Decoder access to the selected archive or raw input is unnecessary.
This diagnostic enumerates serialized bytes, not token-level source sequences;
it establishes no optimality theorem for the representation.

The supplied [Cover reference](https://doi.org/10.1109/TIT.1973.1054929)
attributes enumerative coding; this implementation's exact size identity and
inverse are checked locally. The [contest rules](https://hutter1.net/prize/hrules.htm)
also require executable verification and count the chosen package/option form,
including applicable separate encoder/decoder multiplicities. Their accounting
must be resolved before treating C as a complete prize-facing package.

## Opening250KB result

The [closed corpus receipt](../operations/provenance/dualstream_enumerative_terminal_20260907.json)
records all fifteen successful phases under the published v3 job:

| Arm | Complete archive bytes |
| --- | ---: |
| Plain Deflate P | 89,041 |
| Fixed grammar Deflate B | 102,492 |
| Same grammar enumerative E | 140,524 |
| Same graph, token arguments T | 141,295 |
| Plain byte enumeration R | 160,547 |

Every arm independently reconstructs the exact 250,000 raw bytes and repeats
from its fixed source. E/T preserve B's program graph; their decoded serialized
section hashes match the encoder. B/E/T each retain twelve repeated-argument
references in the third frame. The initial frozen-plan annotation and synthetic
review incorrectly generalized zero bindings from the newer selected grammar
to B's old selection. Those records remain unchanged; this explicit correction
does not change the stored program, controls or measured differences.

E's rank payload alone is 128,666 bytes, already larger than B's entire 102,492
bytes. Eliminating its count tables and headers cannot make these fixed ranks
beat B. This is a bound on this transmitted representation and chunk policy,
not all enumerative or grammar codecs. E adds 38,032 complete bytes over B.

T saves 33,580 literal-definition rank bytes but adds 34,216 argument rank
bytes, 132 count-table bytes and three stream-header bytes: a 771-byte loss.
Programs, structure and content ranks remain unchanged.

The measured E serializer uses 0.840286281 CPU seconds; its independent decoder
uses 0.92072695. The full guarded job records 34,979,840 peak cgroup bytes and
10.0568 elapsed seconds, with no exceeded guards. Timing is diagnostic.
The experiment source union is 56,323 bytes; complete counted package remains
unknown. Prior runner failures and their repairs remain immutable and separate.
Keep the evaluator; park this exact coding realization. A successor must change
the transmitted representation or conditional coding, then measure its own
complete bytes. No confirmation or larger gate is authorized by this loss.

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
byte enumeration R. All use identical raw frame boundaries. Historical selected
programs contain zero repeated argument bindings: T tests argument storage,
while synthetic fixtures alone exercise shared-binding interpretation.

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

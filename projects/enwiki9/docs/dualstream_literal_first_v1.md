# Literal-first grammar codec

This successor tests whether selected exact templates can pay inside ordinary
Deflate. It changes the representation search. The previous event-context and
enumerative configurations remain sealed and parked.

`tools/dualstream_literal_first_v1.py` discovers complete page and LF-delimited
spans in each independent frame. It reuses the existing exact schema proposal
generator, including repeated argument bindings. Unmatched spans remain literal
bytes; neither unique words nor one-off arguments enter a global dictionary.

The fixed search retains at most 1,024 spans and 48 proposals per frame. Each
round measures every remaining eligible proposal against the whole current
frame and accepts the smallest strictly improving result. At most eight rules
are admitted. Overlapping spans are excluded. Counts before and after caps,
every measured candidate, accepted deltas and hashes are retained. This is a
bounded greedy search, not a proof that its final representation is optimal.

The selected representation contains backward-only template definitions,
length-delimited literal runs, calls and arguments. A supplied argument may be
used repeatedly. The interpreter supports nested backward calls with explicit
bindings; this discovery realization proposes direct templates only. Unused
definitions, unused arguments, forward references, excessive work/output,
trailing data and corrupt frames are rejected. No text normalization occurs.

One level-9 Deflate payload encodes the complete selected representation. The
existing 24-byte archive and 57-byte frame headers retain their sizes. Selected
archives use `D2LIT001`; an archive whose frames all fall back uses the exact
existing `D2GRAM02` plain bytes. Frame mode 4 identifies a selected program.
The decoder does no discovery. It also recompresses the decoded representation
to check canonical Deflate bytes; measured decode costs include that check.

Run the implementation on bounded files:

```bash
python3 tools/dualstream_literal_first_v1.py encode input.raw candidate.d2g --mode D
python3 tools/dualstream_literal_first_v1.py decode candidate.d2g restored.raw
cmp input.raw restored.raw
```

The input limit is 1,000,000 bytes, with frames at most 65,536 bytes. Existing
output paths are refused. Corpus runs use the published queue driver and its
separate execution bounds, after ownership publication and fresh admission.

P invokes the unchanged argtokens codec in plain mode. K discovers and measures
proposals with admission disabled, and must produce exactly P. D admits only
positive complete-frame savings. Each repeated encoder starts again from exact
raw bytes. Decoder reports compare all transmitted-program and execution
projections; discovery decisions belong only to encoder reports.

Archive costs are jointly compressed payload plus framing. The separate
`representation_costs` table counts bytes before Deflate and must not be
interpreted as per-category compressed savings. Source/runtime inventory and
complete package qualification are separate. The opening development gate
permits a separately frozen confirmation only when D is strictly smaller than
P; fallback equality grants no confirmation or compression credit. The active
99,000,000-byte complete target remains unproved.

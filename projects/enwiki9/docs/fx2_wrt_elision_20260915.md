# Causal WRT bit elision

Owner `root_wrt_elision`, synthesis lenses 7 and 9. The native window change
lost 631 archive bytes. Dense, sparse and local hidden-feature corrections are
also closed. This candidate uses exact frontend constraints rather than another
predictor fit. It claims no new general coding theorem.

The unchanged native binary predicts and codes every modeled bit. Its counted
vocabulary and dictionary imply a smaller admissible set after some prefixes:
the initial dictionary flag, dictionary continuations, escape continuations and
the word following a case control. Definitions follow the pinned original
`Dictionary::Encode`, `EncodeWord`, `EncodeByte` and code-assignment functions.
The checker accepts a conservative superset of encoder outputs; it does not
assume well-formed XML or use a later raw byte to decide admissibility.

After each decoded bit, narrow the current byte's admissible set. When only one
branch remains, encoder and decoder emit that bit without narrowing the coder
interval. Otherwise use the original parent's exact Q16 count. The eventual
native integration must still call parent Predict and Perceive for **every**
bit, including omitted bits, preserving parent learning and clocks.

For this fixed parent trajectory and sound constraints, omitted event t saves
exactly `-log2(p_t(truth)) >= 0` ideal bits. Every other event retains its count.
The sum is therefore a constructive ideal saving, not merely an oracle ceiling.
Finite interval arithmetic and termination need actual replay; a model change,
parser bug, omitted dependency or unpaid code invalidates a stronger claim.

The finite diagnostic uses exposed raw `[0,250000)`, its 151,210 modeled bytes,
and independently verified pre-truth native counts. It retains the supplied
2,419,360-byte count file and original dictionary as conditional dependencies.
It is not a standalone codec or a complete package score.

Arms are retained P; K with full grammar bookkeeping and no elision; V with only
the transmitted vocabulary; D with vocabulary plus source-proved grammar.
V/D each pay a two-byte version/mode header. P/K archives must match exactly;
K/V/D authoritative grammar states must match on the identical decoded input.
All three arms encode, independently decode, and repeat in separate processes.
No wrong constraint is used as a negative control: it would violate correctness.
The vocabulary-only ablation isolates the additional WRT information.

Ten phases include parent projection and nine codec processes. CPU 3, one
runnable thread, 1GiB memory, zero swap, 256MiB scratch, 600-second aggregate
stop; each phase has a 90-second stop. Six synthetic tests pass, including all
44,880 dictionary codes, every binary byte-prefix interval, dictionary boundary
sizes, truncation, pre-truth rejection, original C++ encoder differential testing
on all byte values and fixed-seed random data, an independent eliding inverse, and nine separate replay processes whose decoders have no source-truth file.

If D beats P and V after its header, freeze separately priced native integration;
that is not authorization for a larger population. Otherwise retain the exact
constraint validity and measured ceiling/result, but park this configuration.
There is no constraint or header adjustment after seeing corpus results.

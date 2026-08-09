# SYMBIONT-16 P64 crossing screen

Candidate: `nncp_symbiont16_p64_cmix21_qm0_v1`

This is a frozen compatibility screen between the receipt-bound full-corpus
NNCP symbol frontend and the existing byte-native cmix21 binary backend. It
does not claim that either parent's score transfers to the composition.

The identical first `1,048,576` big-endian U16 symbols feed three layouts:

- `I16`: the original interleaved high/low bytes;
- `P64`: for each natural 64-symbol block, 64 high bytes followed by 64 low
  bytes;
- `P64R`: the same planes, but each high lane is paired with the next block's
  low lane under a cyclic one-block rotation.

Every layout is exactly inverted after cmix decode. `P64` is encoded twice and
must be byte-identical. The source artifact, compressed backend, decoded bytes,
and all arm archives are hash-bound in the decision receipt.

Promotion requires `P64 <= 4.30` actual payload bits per symbol and a strict
payload win over both `I16` and `P64R`, with exact inverses and decimal-memory
compliance. This only authorizes one native CMIX16 design; it is not full-score
evidence. Any miss retires this byte-layout crossing without endian, block,
plane-width, dictionary, or backend-parameter sweeps.

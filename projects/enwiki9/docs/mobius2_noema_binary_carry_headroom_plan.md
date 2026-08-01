# MOBIUS-2 NOEMA binary-carry hierarchy headroom QH0

Date: 2026-08-01

Proposal: `mobius2_noema_binary_carry_headroom_v1`

Candidate: `mobius2_noema_binary_carry_headroom_qh0_v1`

## Claim boundary

This is the prerequisite hierarchy-headroom certificate required by
`docs/mobius2_architecture.md`. It is not the complete NOEMA Q0, a deterministic
integer decoder, a native Gamma integration, a distant-population result, a
forecast update, or a score claim. Its only question is whether recursively
summarized causal state contains target-scale endpoint428 residual information
that is absent from a matched flat recurrent state.

The terminal explicit-lag model used bytes at lags `1/2/4/8/16/32/64` directly.
This candidate never queries those coordinates. The terminal CHIRON/JANUS model
used a two-layer GRU over each 256-byte patch. This candidate instead represents
the decoded prefix as a binary carry tree and reuses one merge cell at every
tree level.

## Bound population

Use the receipt-bound opening-1M artifacts:

- Exact endpoint428 P1 trace and parent archive.
- Exact WRT store and raw inverse.
- Exact page map.
- Official dictionary and inverse backend.

Split the 171 complete pages chronologically by page count:

```text
development          first 3/5
selection            next 1/5
sealed_confirmation  final 1/5
```

Each page is divided from its WRT start into complete 128-byte patches. The
model resets at every patch. Incomplete page tails and bytes outside complete
pages retain the parent P1 exactly. Model weights are fit only on development
patches. Selection chooses one of eight frozen epoch checkpoints. Sealed
confirmation is read only after that checkpoint has been selected.

## Frozen model package

Both learned controls have exactly the same tensor shapes:

```text
byte embedding       257 x 32
leaf projection       32 -> 48
level embedding        7 x 8
shared GRUCell         input 56, hidden 48
node readout            48 -> 255
```

The optimizer is AdamW with learning rate `0.002`, weight decay `0.000001`,
gradient norm clipping at `1.0`, batch size `16`, eight epochs, and seed `428`.
The training objective is truth-bit binary cross entropy after adding the
candidate residual to the exact parent logit. Equal selection payloads choose
the earlier epoch.

Each selected model is symmetrically quantized to signed int8 per tensor, with
one little-endian float32 scale per tensor. The oracle reloads the dequantized
float32 tensors before producing probabilities. Canonical tensor serialization
uses sorted ASCII tensor names and fixed little-endian dimensions and scales.
Two complete fits must produce identical model bytes, adjusted P1 rows, payload
bytes, selection histories, and selected epochs.

The matched package charge is:

```text
max(zlib9(N1 model), zlib9(N2 model))
+ 65,536-byte decoder allowance
+ 32-byte framing allowance
```

The complete charge must not exceed 131,072 bytes. Charging the maximum to both
models prevents compressed-parameter noise from deciding the architectural
control.

## Controls

### N0: exact parent replay

Range-encode the complete WRT truth stream from the exact P1 trace. The result
must be byte-identical to the arithmetic payload in the receipt-bound archive.

### N1: matched flat recurrent state

Before each byte, predict from one 48-wide state. After decoding the byte,
project its embedding and update the state with the shared GRUCell using level
embedding zero. Reset the state at each 128-byte patch. The unused level
embeddings remain in the transmitted package so N1 and N2 have identical
tensor shapes.

### N2/NM: recursive binary-carry hierarchy, memory disabled

Before each byte, sum the occupied tree states and divide by the square root of
the occupied-state count. The node readout maps that aggregate to 255 binary
prefix residuals.

After decoding a byte:

1. Project its embedding to a 48-wide leaf summary.
2. If level zero is vacant, store the summary there.
3. Otherwise merge its older left summary and the newer right summary with the
   one shared cell:

   ```text
   merged = GRUCell(concat(right, level_embedding[level]), left)
   ```

4. Clear that level and carry the merged state upward until a vacant level is
   found.

Seven merge-level embeddings cover the complete 128-byte patch. Surprise
memory is disabled, so this control is both N2 and the required NM ablation.
A headroom miss cannot be rescued by adding surprise memory.

### NS: page-rotated summary-state control

Run the frozen N2 model normally and retain its pre-readout aggregate state for
every modeled byte. Within each chronological split, cyclically rotate source
page identity by one. Preserve byte offset inside a patch and map patch index
modulo the source page's patch count. Apply N2's unchanged readout to those
rotated states. NS is a specificity null only and is not a decoder candidate.

## Exact accounting and proof

Construct and terminate actual range-coded payloads for N0, N1, N2, and NS.
Also construct terminated development, selection, and sealed substreams from
their modeled patches. Normalize each split by the exact raw bytes occupied by
its page-map records, conservatively including the raw equivalents of ignored
patch tails.

The full N2 payload must decode to the exact WRT truth. Rebuild the five-byte
WRT store, run the official inverse backend with the bound dictionary, and
require the exact raw byte length and SHA-256. A second range encoding must be
byte-identical.

## Promotion and kill gates

QH0 passes only if all conditions hold:

```text
parent payload identity                         exact
development N2 gain                             positive
selection N2 gain                               positive
sealed N2 gross gain                            >= 3,000 B/M
sealed N2 gain after matched package allowance  >= 2,100 B/M
sealed N2 payload                               < N1 payload
sealed N2 payload                               < NS payload
matched package                                 <= 131,072 bytes
model/P1/payload/history repeated hashes         identical
full arithmetic decode                           exact
WRT reconstruction and official raw inverse      exact
second archive payload                           byte-identical
```

A pass authorizes one frozen distant reset-population replay and implementation
of the exact dyadic integer runtime. It does not authorize 10M, native Gamma,
100M, or score credit.

A miss retires this exact binary-carry construction without patch-size, level,
state-width, embedding-width, optimizer, epoch, aggregation, quantization, or
rotation sweeps. It does not retire a semantic-boundary hierarchy, a transmitted
LOGOS grammar, or a materially different sparse context DAG.

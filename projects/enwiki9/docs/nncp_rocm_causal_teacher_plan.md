# ROCm-native causal symbol teacher

Status: proposed target-bearing teacher experiment; zero score credit.

## Boundary

This is not a LibNC port and makes no claim of reproducing NNCP's published
CUDA archive. The native CUDA trace route is operationally closed because this
workspace has no NVIDIA machine. The ROCm teacher is a new causal probabilistic
model whose value must be established by its own exact arithmetic archive.

The completed full-corpus preprocessing gate supplies:

```text
raw bytes                 1,000,000,000
preprocessed symbols        200,608,961
minimum symbol                        1
maximum symbol                   16,384
required vocabulary              16,385
padded vocabulary                16,392
dictionary bytes                186,264
```

All teacher and Gamma comparisons use the frozen raw/symbol windows in
`results/nncp_full_symbol_map_v1/window_manifest.json`.

## Frozen Q0 architecture

There is one architecture, not a width or depth sweep:

```text
symbol vocabulary        16,392
layers                        20
model width                 1,024
attention heads                 8
head width                    128
feed-forward width          3,072
segment length                 64
detached memory               256 symbols per layer
normalization                 pre-RMSNorm plus final RMSNorm
activation                    GEGLU
parameter/activation dtype    BF16
reductions and loss           FP32
dropout                       disabled
```

Use a standard explicitly causal relative-position or ALiBi attention rule
implemented for ROCm. It need not imitate LibNC's relative shift. The rule,
mask, memory update, parameter initialization, optimizer, and coder are part of
the new teacher definition and are hash-bound before holdout.

## Causal schedule

For segment `j`:

1. Inputs contain only symbols preceding each target.
2. Persistent layer memories contain only earlier completed symbols.
3. The model emits the complete distribution before observing each target.
4. Exact integer arithmetic frequencies are derived and the segment is coded.
5. Only after all segment predictions are fixed may the true segment update
   model parameters.
6. Memories and optimizer state advance by a fixed operation count.

Compression and decompression start from the same seed, parameters, optimizer,
and empty memories. No teacher checkpoint, hidden state, gradient, or future
symbol is transmitted.

## Exact coder

Use NNCP's published binary split construction as a separately implemented
coder contract:

```text
PROB_UNIT = 32768
prob0 = clamp(round(left_mass * 32768 / active_mass), 1, 32767)
```

The exact rounding operation, tree order, range renormalization, carry handling,
and finalization are frozen before the first archive comparison. Trace-on and
trace-off must produce identical archives. Decompression must reconstruct the
preprocessed symbols and the official inverse must reconstruct the raw input.

## Gates

### Q0: bounded construction

On a fixed 65,536-symbol population:

```text
causal-mask audit                 pass
finite normalized distributions  pass
trace-on/off archive identity     exact
symbol roundtrip                  exact
raw inverse                       exact
deterministic second archive      exact
frozen environment/model hashes  present
```

This gate establishes execution only and receives zero score credit.

### Q1: first mature headroom

Run continuously from symbol zero through the frozen
`mature_9m_10m` endpoint. Compare exact shadow-finalized teacher and Gamma
archive deltas on the inward-snapped raw window.

Require:

```text
teacher advantage >= 3,000 B/M
continuous state from byte zero
same raw population
exact archive and inverse identity
```

Failure retires this architecture and the ROCm teacher lane. Do not respond
with depth, width, dropout, optimizer, or learning-rate sweeps.

### Q2: transfer and cumulative headroom

Only after Q1 passes, extend the same state trajectory to the frozen
49M-50M and 99M-100M windows. Authorization for quotient work requires at
least two mature windows at or above `3,000 B/M` and positive cumulative
advantage through 100M.

## Student boundary

Teacher success authorizes only `QUOTIENT-BUDGET-CERT`. It does not authorize a
student implementation or score claim. The final student remains a separately
counted deterministic CPU program and must satisfy the 108,000,000-byte target,
roundtrip, runtime, and memory constraints.

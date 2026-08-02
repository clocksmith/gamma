# NNCP v3.3 LibNC tanh-GELU online-update parity

Proposal and candidate:
`nncp_v33_libnc_tanh_gelu_online_update_parity_v1`.

The primitive gate identifies LibNC `nc_gelu` as an unfused F32 tanh GELU,
including its positive-tail saturation. The old parity tool used PyTorch's
default exact-erf GELU. This candidate changes only that activation contract
and replays the same receipt-bound one-layer, width-32, four-symbol,
single-update miniature.

Inputs, seed, coefficients, teacher trace, optimizer, learning rate, per-tensor
gradient clipping, and `2e-5` threshold remain unchanged. The corrected replay
runs twice from the same serialized initial tensors and requires identical
final-tensor hashes.

Promotion requires:

- Initial maximum distribution error no greater than `2e-5`.
- Every named final parameter within `2e-5` of the LibNC export.
- Maximum final parameter error no greater than `2e-5`.
- Repeated final-tensor hash equality.

A miss retires tanh GELU as a sufficient fix. A pass only authorizes the next
frozen parity gate; it gives zero score credit and does not authorize mature
training or compression.

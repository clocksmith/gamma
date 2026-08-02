# NNCP v3.3 LibNC RMSNorm backward parity

Proposal and candidate: `nncp_v33_libnc_rmsnorm_backward_parity_v1`.

The direct GELU gate found and corrected one real mismatch, but the bound
miniature full update still diverged at the first-step Adam sign ceiling for
internal attention, feed-forward, embedding, and normalization parameters.
This gate isolates the next shared primitive: LibNC `nc_rms_norm`.

Compile one C probe against the receipt-bound LibNC header and shared library.
On a frozen 5-column by 8-feature F32 matrix, capture all RMSNorm outputs and
input gradients under a nonuniform frozen upstream gradient. Repeat the probe
and require byte-identical stdout.

Compare the direct bytes with exactly three preregistered contracts:

```text
current     x * rsqrt(mean(x^2) + eps)
outside     x / (sqrt(mean(x^2)) + eps)
sum form    x * sqrt(n) * rsqrt(sum(x^2) + eps)
```

The tiny-valued column makes epsilon placement identifiable. A contract must
match both values and gradients within `2e-6` maximum absolute error.

- A unique current-contract match retires RMSNorm as the remaining cause.
- A unique alternative match authorizes one corrected bound miniature update.
- Nondeterminism or malformed gradient capture is infrastructure failure.
- No unique match authorizes only operation-order localization, not a model
  run.

The gate has zero score credit and cannot move the forecast or inherit NNCP's
published result.

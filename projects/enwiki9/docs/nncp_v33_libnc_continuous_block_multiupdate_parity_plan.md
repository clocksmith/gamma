# NNCP v3.3 LibNC continuous-block multi-update parity

Candidate: `nncp_v33_libnc_continuous_block_multiupdate_parity_v1`

The prior native multi-update test used `block_len=4`, so every update entered
a new `process_block`, reset persistent memory, and used input zero at state
zero. The published profile instead retains state across many updates within a
long block. Test that missing contract by changing only native `block_len` from
4 to 32 for the same 32-byte, batch-one, four-state miniature.

The analytic replay carries the preceding truth symbol and `mem_h` across all
eight updates. Retain the proved concat-RMSNorm backward, tanh GEGLU, gradient
clipping, and Adam rules. Capture all native post-update parameters, `train_h`,
and `mem_h` twice.

Require exact repeated native archive, probability trace, and state files;
exact repeated analytic tensors; legal aligned probabilities; maximum
probability and parameter errors at or below `2e-5`; and maximum `train_h` and
`mem_h` errors at or below `2e-6`. A pass authorizes only the smallest
source-bound continuous-profile prefix gate. A miss retires this exact carried-
state contract without block-length, memory-length, width, optimizer, clipping,
epsilon, or tolerance sweeps.

The candidate has zero score and forecast credit. Forecast remains
`109,389,323` bytes and the verified full-1G score remains unknown.

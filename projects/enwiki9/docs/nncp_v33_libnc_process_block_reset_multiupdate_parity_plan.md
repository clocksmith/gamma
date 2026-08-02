# NNCP v3.3 LibNC process-block reset multi-update parity

Candidate: `nncp_v33_libnc_process_block_reset_multiupdate_parity_v1`

## Frozen correction

Retain the analytic concat-RMSNorm backward, per-parameter gradient clipping,
and Adam update. Change only the segment schedule to match native execution:

```text
for each four-symbol process_block:
    memory = zeros(4, 32)
    inputs = [0, truth_0, truth_1, truth_2]
    predict four truths
    update parameters once
```

The produced `train_h` and post-update `mem_h` are compared with source state,
but neither is carried into the next process block.

## Gate

Two native captures must repeat and remain byte-identical to the parent archive,
teacher trace, and update-state files. Two analytic runs must repeat. Across all
eight updates require:

- probability maximum absolute error at or below `2e-5`;
- every named post-update parameter at or below `2e-5`;
- `train_h` and post-update `mem_h` at or below `2e-6`;
- legal finite probabilities and exact truth alignment.

A pass authorizes only the smallest faithful-profile constructive prefix gate.
A miss retires this exact block-reset schedule without reset, block-length,
memory-length, width, optimizer, clipping, epsilon, or tolerance sweeps. The
candidate has zero score and forecast credit; forecast remains `109,389,323`
bytes and the verified full-1G score remains unknown.

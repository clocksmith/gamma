# NNCP v3.3 LibNC softmax-indexed-log backward parity

Candidate: `nncp_v33_libnc_softmax_indexed_log_backward_parity_v1`

Status: frozen zero-credit implementation-parity diagnostic.

## Question

Does LibNC's explicit `softmax -> indexed_log -> sum -> mean scaling`
backward graph produce per-logit gradients that differ from PyTorch fused
cross-entropy enough to explain cancellation-amplified sign reversals behind
the otherwise exact output layer?

## Frozen fixture

The direct LibNC probe uses 256 classes, four columns, targets
`[60, 109, 101, 100]`, and deterministic modular F32 logits. It serializes all
1,024 probabilities and all 1,024 logit gradients. Two executions must produce
an identical aggregate SHA-256.

## Frozen comparisons

- PyTorch fused mean cross-entropy.
- PyTorch explicit softmax, indexed probability, log, sum, and mean.
- The closed-form `(probability - onehot) / 4` gradient.

Every contract includes the same softmax probabilities. The absolute
probability and gradient threshold is `2e-6`.

## Decision

A unique non-fused match authorizes one bound miniature replay changing only
the loss backward. A fused match, no unique alternative, nondeterminism, or a
threshold miss retires this loss graph as the cause. Logits, targets, loss
scaling, and tolerance are frozen and are not swept.

This diagnostic has zero score and forecast credit. The planning forecast
remains `109,389,323` bytes and the verified full-1G score remains unknown.

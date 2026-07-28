# ROCm Batched Causal Teacher Decision

Verdict: REJECT

Score credit: 0 bytes

Candidate: `nncp_rocm_batched_causal_teacher_v1`

## Causality correction

The prior batched-teacher rejection used the wrong shifted-input boundary.
Changing target symbol 8 changes model input 9. It may therefore change
prediction 9, but not predictions 0 through 8.

The corrected audit passed:

```text
dependency graph isolated                       true
maximum output 0..8 error                       0.0
legal output-9 change                           1.046875
batched/incremental maximum probability drift   9.886134648695588e-7
```

The teacher is causally legal as an offline oracle. Batched and incremental
numerics are not identical, so it is not a constructive decoder.

## Q0 exact teacher receipt

Job: `20260728T190645Z_92e9ab4189`

```text
symbols                         65,536
raw bytes                      322,978
payload bytes                   90,931
payload SHA-256
2fbe629b174dbf0aba09d918e490c5df1a4fdeff3673fa1c8ae9d1a8503dab4d
parameters                 306,402,312
maximum prefix error               0.0
deterministic second archive       true
official raw inverse               true
symbol identity                    true
peak ROCm allocation        6,225,571,840 bytes
```

At the exact shared boundary:

```text
Gamma bits                    468,490.156
teacher bits                  727,447.033
teacher minus Gamma           -32,369.610 bytes
```

## Q1 maturity receipt

Job: `20260728T192225Z_cf78d7cfa0`

```text
symbols                        102,871
raw bytes                      500,000
payload bytes                  139,677
maximum prefix error               0.0
official raw inverse               true
symbol identity                    true
```

At the shared 499,986-byte boundary:

```text
Gamma bits                    709,051.816
teacher bits                1,117,396.064
teacher minus Gamma           -51,043.031 bytes
```

The new 177,008-byte band after Q0 produced:

```text
marginal teacher gap          -18,673.421 bytes
marginal rate                -105,494.788 B/M
required authorization rate    +3,000.000 B/M
```

## Decision

The corrected ROCm teacher is causal and reproducible, but it is not a useful
teacher for Gamma. Its marginal performance worsens the deficit instead of
converging toward target-scale headroom.

Reject the architecture unchanged. Do not run the 1M, 10M, or 1G extensions. Do
not train a quotient or student. Do not sweep width, depth, vocabulary,
precision, learning rate, optimizer, memory, or segment length.

This does not contradict published NNCP results because this ROCm model is not
LibNC-equivalent and makes no LibNC parity claim.

# CHIRON Frozen Residual LM Q0 Decision

Verdict: REJECT

Score credit: 0 bytes

Candidate: `chiron_frozen_residual_lm_q0_v1`

Job: `20260728T185712Z_43dab2487d`

## Binding

```text
p1 SHA-256
a37c80c4167ef0c26bc3b8884de93c0a12224e8113e00ad1e33bfaf3fad1b898

WRT SHA-256
1e209c7d19a22af5ce6a1de3bab1fc636669f40686aebd88bbe9dc8e5411e583

WRT bytes                  600,742
complete scored WRT bytes  600,576
parent payload expected    173,859
parent payload replayed    173,859
```

The exact parent trace replay passed before training or candidate scoring.

## Fixed construction

```text
causal reset block          256 WRT bytes
embedding width              64
GRU hidden width             96
GRU layers                    2
binary-prefix outputs       255
parameters              143,711
epochs                        8
quantization            int8 per tensor, dequantized for oracle execution
```

The chronological split used 1,642 training blocks, 351 development blocks,
and 353 holdout blocks. No holdout-dependent architecture choice was made.

## Exact decision

```text
                              baseline  candidate  gain
development                     25,593     25,602    -9
holdout                         23,417     23,424    -7
holdout node-bias control       23,417     23,478   -61
holdout circular-shift null     23,417     23,463   -46
```

```text
gross holdout rate              -46.534 B/M
int8 tensor certificate         141,601 bytes
compressed oracle source          5,455 bytes
provisional package             147,056 bytes
package amortization            147.056 B/M
net holdout rate               -193.590 B/M
required gross rate            3,000.000 B/M
required net rate              2,100.000 B/M
```

CHIRON beat the two negative controls but did not beat the parent. Its
development loss also worsened after the first epoch, while training loss kept
falling, showing direct overfit rather than hidden transferable headroom.

## Consequence

Reject compact frozen recurrent endpoint correction trained directly on
opening-trace residuals at this information scale. Do not reopen it through
width, depth, block length, precision, optimizer, or epoch changes.

This result does not authorize a deterministic integer decoder, native
integration, distant transfer, forecast movement, or score credit.

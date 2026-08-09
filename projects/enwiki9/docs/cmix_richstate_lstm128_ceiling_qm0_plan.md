# cmix-obias Rich-State LSTM128 Ceiling Qm0

Status: frozen exact capacity gate; zero score credit until native archive replay

## Question

Can added capacity on the donor's unusually rich causal residual state improve
over its paid 32-cell head by enough to close the `105,000,000` target, after
paying the larger model twice and preserving a `500,000`-byte reserve?

The external H32 report is only about `903` bytes per modeled MB. The frozen
H128 gate requires `7,816` additional bytes per modeled MB. This is deliberately
one target-derived capacity point, not a width sweep.

## Frozen construction

Use the donor's exact `res_v3` trace: discretized base probability, truth bit,
override flag, 25 stage-1 inputs, and raw terminal-mixer output. Rebuild the
documented 92 causal features. Keep the receipt-bound fp16 H32 head frozen and
add an independent H96 branch with zero output initialization. Their summed
logit is a block-diagonal 128-cell realization that begins exactly at H32.

Train the H96 branch once on block 0. Block 1 is development-only. Blocks 2,
3, and 4 are three disjoint confirmation populations. All blocks contain
`1,048,576` coded bits and preserve the donor's 64-bit reset geometry. Round
the learned branch through fp16 before scoring.

For each arm, discretize to the donor's u16 probability and replay its exact
32-bit range update with independent block termination. Override bits retain
the base probability. Report both ideal entropy and finite bytes.

## Accounting and decision

The dense fp16 blob formula is `24 + 2*(8H^2 + 103H + 1)`. H32 costs `23,002`
bytes and H128 costs `288,538`; replacing H32 therefore adds `531,072` counted
bytes when charged twice. Together with the external parent's `3,492,825` debt,
`500,000` reserve, and `65,000` source allowance, gross full-stream gain must
reach `4,588,897` bytes, or `7,816` bytes per million modeled bytes.

Promote only if finite H128-minus-H32 gain reaches that rate and every
confirmation block is positive. Otherwise retire wider rich-state residual
heads without width, reset, feature, optimizer, or epoch rescue sweeps.

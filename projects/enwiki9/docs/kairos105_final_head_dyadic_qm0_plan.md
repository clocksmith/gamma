# KAIROS-105 final-head dyadic opening gate

## Boundary

This candidate leaves the raw input, preprocessing, modeled arithmetic-bit
stream, Predictor state, BitLSTM32 state, update order, and inverse unchanged.
It observes the exact post-BitLSTM probability immediately before arithmetic
coding. Raw arithmetic calls are recorded explicitly and never corrected.
Override bits are also left unchanged.

The opening scope is the first 1,000,000 raw bytes. It validates instrumentation,
candidate-independent features, paid schedules, controls, and exact finite
range replay. It cannot authorize a native child or claim full-corpus transfer.

## Frozen representation

The correction is a rank-eight Q8 affine field. Features are:

1. intercept;
2. centered final probability;
3. raw final-mixer logit;
4. FXCM stage-one input;
5. byte-LSTM stage-one input;
6. mean of the 23 layer-zero mixer outputs;
7. layer-zero mixer spread;
8. byte-LSTM minus FXCM disagreement.

Atomic leaves contain 262,144 arithmetic bits. Every dyadic node receives one
Newton correction from additive gradient/Hessian statistics, clipped and
quantized to signed Q8. A deterministic dynamic program chooses KEEP or SPLIT.
Selection charges one flag byte and sixteen raw coefficient bytes per retained
rank-eight leaf. The final receipt additionally counts the exact compressed
schedule, deterministic lookup material, and compressed source package.

## Arms

- `B0`: unchanged post-head probabilities.
- `G0`: one global paid rank-eight correction.
- `K0`: paid dyadic rank-eight field.
- `P0`: paid dyadic intercept-only calibration control.
- `R0`: K0 leaf coefficients rotated by one leaf.
- `S0`: K0 leaf coefficients deterministically shuffled within length groups.
- `O0`: independent atomic-leaf corrections with identities and cost supplied
  free; ceiling only.

## Opening decision

The traced donor payload must be byte-identical to the frozen donor payload.
Replaying B0 through the recorded complete arithmetic-call stream must reproduce
the native range-coded suffix exactly. Every candidate payload must decode to
the recorded truth sequence. The K0 schedule and payload must repeat exactly.

Scaled discovery references are 4,500 gross bytes and 500 bytes over each
matched control on 1M raw. These references do not promote the candidate. A
healthy opening only authorizes construction of the compact full-stream
statistics observer and a fresh exact full-stream replay.

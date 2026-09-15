# Online learning on the frozen transformer

`fx2_online_head_opening250k_v1` tests a larger predictive change than the
34-byte expert mixture. It does not inherit that gain, the NNCP MIDAS teacher's
gain, or external full-corpus scores. Projected online logistic learning is
established machinery; applying it here is an experiment, not a novelty claim.

The fixed FX2 model provides a192-dimensional normalized hidden vector and205
post-softcap logits. Define phi=h/sqrt(1+sum(h_i*h_i)). A205-by192 correction
matrix A starts at zero. After each actually decoded next-token label y:

    q = softmax(base_logits + A phi)
    A <- A + (1/4) (onehot(y) - q) phi^T
    if ||A||_F > 4: A <- A * (3.999999 / ||A||_F)

The first prediction after reset uses the original probabilities exactly.
The matrix resets at the original article/piece boundaries. No deep weights,
KV cache, KDA transition, dictionary or token geometry changes. Downstream CMIX
models consume the corrected neural probabilities and may learn differently.

The hook observes decoded truth before the existing separator test. This trains
on the last token of a piece even though the original transformer skips its
forward pass. First tokens predicted only by PPM have no pending head update.
This alignment is essential to causal validity.

In real arithmetic, the conditional negative log likelihood is convex in A,
with gradient (q-onehot(y))phi^T. Cauchy-Schwarz gives |(A phi)_j|<=4 after
projection. These facts describe the update and its bounded strength; they do
not prove fewer archive bytes. Stored state is binary32, with ordered binary64
norms, dot products and softmax calculations under the bound toolchain. Exact
same-host encode/decode/repeat comparisons and explicit numerical checks test
that implementation. Cross-machine qualification remains separate.

The matrix occupies157440 state bytes; all parameters start procedurally at
zero. No training trace or offline learned adapter is sent to the decoder.
P leaves the head unchanged. K trains a shadow matrix but emits P. D emits its
aligned correction. S trains on cyclically wrong labels, with identical shapes,
features, resources and update timing. K/D introduced states must be identical;
P/K archives and coder trajectories must match the retained native parent.

The gate covers exposed opening250KB, with one fixed configuration. Complete
introduced state is recorded at2048 decoded-byte boundaries and termination.
SHA256 block digests cover every frozen hidden vector and base logit. All arms
must reproduce these same digests; all independent inverses and repeats must
pass. An untraced D encode must reproduce traced D exactly.

A valid nonpositive P-D or S-D rejects this configuration. A positive result
still requires actual delivery costs, independent confirmation and later joint
scaling. Correctness, control or resource failures provide no compression-loss
verdict. The90,000,000-byte target and verified full-corpus score remain unproved.

[Contract](../operations/adaptive/experiments/fx2_online_head_opening250k_v1.json)
[Plan](../operations/provenance/fx2_online_head_opening250k_v1_plan.json)
[Core](../lib/fx2_online_head_v1.hpp)

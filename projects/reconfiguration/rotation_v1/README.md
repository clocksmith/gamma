# Rank-two request-local rotation v1

This is a separate experimental operator candidate, not a modification of frozen
channel-gain results. Gamma owns this evidence/replay contract; Doppler owns GPU
capture and arithmetic in `src/gpu/kernels/channel-rotation.js`.

For each explicitly selected dense layer, capture signed post-SwiGLU instruction
and original-context complement means in one prefill. Normalize the instruction
mean as u, remove its projection from the reference mean and normalize that as v.
An absolute configured epsilon makes zero/collinear means an explicit identity;
invalid/overflowing data rejects, including recorded-command validation.

Apply R(theta) a = a + u[(cos(theta)-1)(u.a)-sin(theta)(v.a)]
+ v[(cos(theta)-1)(v.a)+sin(theta)(u.a)] before the down projection.
This mixes channels, preserves norm in exact arithmetic, has inverse R(-theta),
and is equivalent to a rank-at-most-two update of W_down. It does not mutate
shared weights. Theta zero is the base operator. Storage is 2*d f32 values and one
status scalar per layer (8*d+4 logical bytes), plus ordinary output/work buffers.
Capture reads the declared content span; application is O(d) per token, with GPU
reductions/barriers. These complexity facts are not end-to-end speed evidence.

`operator.mjs` seals exact little-endian f32 plane bytes, executed f32 angle and
epsilon, layer, model/prompt/capture/shader hashes and runtime commit. Replay
checks structure, orthonormality and hashes. This is inspectable configuration
reconstruction, not a strict quine, proof of trusted authorship, independently
verified provenance, retained learning or RSI. Serialize only with authorization
for the underlying prompt-conditioned information. Changing model, prompt or
capture contracts requires a new record; a hash does not validate a claimed ID.

## Acceptance and remaining work

CPU reference and physical GPU tests live in Doppler:
`tests/kernels/channel-rotation-reference.test.js` and
`tests/kernels/channel-rotation-physical.test.js`. They check independent
numerics, immediate/recorded parity, zero identity, inverse, input immutability,
degenerate identity and invalid-data rejection. Toy timings include setup and
synchronization and do not estimate model adaptation overhead.

Run `node projects/reconfiguration/rotation_v1/test_operator.mjs` for exact
replay and corruption checks. This directory contains no model result.

Before a model run: wire signed-mean capture and frozen operator ownership into
the experimental dense FFN request lifecycle, explicitly distinguish base-cache
first logits from re-prefill, and test reset/cancellation/isolation. Choose a
capable model using development tasks, freeze layer/angle candidates, task
population and total budget, and compare zero, both angle signs, diagonal gain,
matched random-plane and shuffled-task controls. Include setup/readback,
re-prefill, decode, verifier and memory costs, plus matched-compute base sampling.
Confirmation outputs must be sealed before reserved semantic evaluation.
No optimum, specialization benefit, novelty, cross-domain gain or AGI is claimed.

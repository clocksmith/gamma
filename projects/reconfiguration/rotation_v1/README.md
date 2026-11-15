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

Doppler now exposes `beginChannelRotationRequest(spec)` on the loaded pipeline.
It shares the gain request's guarded operation, reset and cancellation lifecycle,
not a second competing session state. Capture uses `rotationEpsilon` and
`captureContentSpan`; `takeRotations()` transfers basis/status ownership after
prefill settles. `freezeChannelRotations([{layerIdx, channels, theta, rotation}])`
privately copies and validates those buffers. Apply uses the handle through the
historical `frozenGains`/`gainHash` fields; the opaque handle also binds its kind.
Angles and copied planes cannot change through the public seed tensors.

The request selects explicit split gate/up on selected layers so post-SwiGLU
activation exists before down projection. Include the resulting loss of fusion
in costs. The zero-angle arm uses that same split path; also retain ordinary
no-request base as a separate performance comparator. Unsupported fused stored
weights, MoE, batching, chunked prefill, LoRA and non-f32 activation reject.
Base-cache attaches after unmodified prefill: its first-token logits are base.
Re-prefill applies the frozen plane to the new full prefill. Neither promises
cache equivalence. Request close/reset releases its borrow; the handle cannot
close while another request uses it. Recorded work must settle or abort first.

Run `node model_smoke.mjs DOPPLER_ROOT LOCAL_MODEL` from this directory for a
bounded full-model integration probe: synthetic exact token halves, one selected
last layer, zero/positive/negative angle, both cache arms, a single decode step,
and reset comparison. It is not a quality workload, benchmark or held-out test;
local generated receipts are not implicitly authorized for publication.

Next choose a capable model using development tasks, freeze layer/angle candidates, task
population and total budget, and compare zero, both angle signs, diagonal gain,
matched random-plane and shuffled-task controls. Include setup/readback,
re-prefill, decode, verifier and memory costs, plus matched-compute base sampling.
Confirmation outputs must be sealed before reserved semantic evaluation.
No optimum, specialization benefit, novelty, cross-domain gain or AGI is claimed.

`development_screen.mjs DOPPLER_ROOT LOCAL_MODEL LOCAL_RECEIPT_PREFIX` is a
prespecified 12-item cross-domain development screen. It freezes its protocol
before loading a model, gates on non-floor/non-ceiling base accuracy, and compares
zero, both fixed signs, cyclic other-task planes and a seeded model-independent
plane. It scores only the supplied A/B/C/D token logits, not free-generated
answers. Inputs are explicitly concatenated token segments. Expected random
choice accuracy is 25%; one fixed random-plane control is not a distribution of
random controls. No task or angle is replaced after results.

Per-request times charge capture, freezing, re-prefill, scoring and reset. Cold
model load is separate; fixed random fixture construction and tokenization are
shared setup and not included in those per-request totals. These are diagnostic
wall times from one sample each, not a counterbalanced speed benchmark. Reused
capture costs are charged again to each hypothetical independent request; summing
arm totals is therefore not the physical duration of the shared run. Keep raw
protocol/results local unless separately authorized to publish them.

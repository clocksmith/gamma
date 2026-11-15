# Prospective channel-gain reference

Status: CPU reference and prospective runtime integration. No model run, fresh
quality result, physical GPU qualification, latency improvement or RSI is established.
Historical protocols, runtimes, exposed tasks and result records are unchanged.
Parent contract: [request-specific reconfiguration](../CATSCAN.md).

## What is implemented

`samePassEnergy` consumes original full-prompt post-SwiGLU activations one token
row at a time. It separately accumulates squared energy for the exact instruction
span and the remaining content tokens. Chat-template tokens are excluded. Each
layer must have its own accumulator and gain vector; channels across layers are
not interchangeable. Retained accumulator storage is two float64 arrays per
layer, independent of prompt length. This is a numerical reference, not a design
that sends GPU activation rows to the CPU during inference.

`deriveGains` implements:

    score[i] = (instructionEnergy[i] - referenceEnergy[i]) / (referenceEnergy[i] + epsilon)
    logGain[i] = beta * clip(score[i], -clip, clip)
    gain[i] = exp(logGain[i] - mean(logGain))

It validates shape, finiteness and nonnegative energies. Beta zero is an exact
identity; reversing beta reciprocates gains. Application is still an immutable
request-local multiplier before the down projection, equivalent to multiplying
columns of the down-projection matrix. It neither learns nor persists successors.

## Separate hypotheses, not an edit to reference A

1. Historical reference A performs a separate prefill with instruction tokens
   removed. Preserve it as the comparator with its full setup costs.
2. Same-pass complement uses original token positions and contextual states from
   the complete prompt. Reference tokens after the instruction can depend on it.
   It therefore tests a different signal, not an equivalent optimization.
3. A fixed unrelated reference can use `deriveGains`, but is NOT implemented as
   a production artifact loader here. An artifact must bind model revision,
   executed precision, exact layer/channel ordering, tokenizer/template, prompt
   hashes, energy computation and aggregation. Its one-time creation costs must
   be reported separately from request costs. No reference artifact exists here.

## Next experiment integration

The CPU tests qualify math and streaming capture only. Doppler commit `1b76eee0` implements a GPU reduction of both spans from the same
activation tensor through the existing request lifecycle. Its physical test
exists but has not run in this session; compare it against this reference before
model execution. Do not read full activation rows back into the serving loop.
Keep historical GPU capture and frozen study source locks unchanged.

Create new tasks from previously unexposed families, with the SAME explicit
interface scaffold in all arms. Qualify independent oracles with known-correct
and plausible-wrong sources. Separate development/selection from sealed
confirmation before generation. Do not relabel the two successful scaffold
examples as fresh tasks.

In independent selection, compare real base, beta=0, beta=+0.05 and beta=-0.05
with clip=1 and epsilon=1e-6 first. Report actual model layers, not an unqualified
claim that the final two are optimal. Freeze any subsequently selected layer set
and strength before confirmation. Confirmation includes permuted-gain,
random-transform and shuffled-instruction controls, with matched sampling and
compute alternatives. Run reference A and same-pass as distinct named rules.

Report base-cache and re-prefill separately. In base-cache, first-token logits
are unchanged; tasks must exercise subsequent transformed decode. For re-prefill,
freeze gains from the original prefill, then rebuild cache without recomputing
gains. Release an unused base snapshot in a new serving-only path, never silently
subtract its storage from the existing harness receipts.

Measure cold load, reference/base/second prefill, derivation, decode, reset and
end-to-end time, plus retained and peak memory. Charge setup and controls honestly;
measure instrumentation overhead. Preserve service guards and hardware ownership.
No GPU run is authorized by reading this document alone. Run only through the
owner-approved executor with accessible hardware and pinned source/artifact locks.

## Focused check

    node --test projects/reconfiguration/gain_reference_v1/test_rule.mjs

## Executable selection harness

`selection.mjs` now provides `selectionSchedule` and `executeSelection` for the
existing native runtime API. Per task it executes ten arms: real base, exact
zero-beta gain, positive/negative gains, and permuted/random/shuffled controls
for each nonzero candidate. Arm order rotates across tasks; this is partial
counterbalancing, not complete order balance unless enough tasks are supplied.
Each arm pays for its own preparation. All physical preparation receipts are
retained; do not mistake a selected arm's attributed cost for total experimental
cost. Memory baseline subtraction may be unavailable when a transformed arm
precedes base; absolute memory remains reported, with no inferred subtraction.

The executor admits reference A and the separately named same-pass complement
rule. Each run must use one reference hypothesis and an explicitly capable
runtime. It rejects mixed layer sets because runtime geometry is fixed at
creation. Run separate locked instances for layer ablations.
It requires resource/source admission, exact prompt/schedule hashes, explicit
sampling seed, memory/timing receipts and durable output sealing before scoring.
It rejects confirmation populations. There is deliberately no self-authorizing
GPU launch or default admission callback.

`development_tasks.mjs` constructs three public selection families with explicit
scaffolds: inclusive prefix sum, stable rank and periodic second difference.
The host-side expected values have independent hand-calculated examples, and
public checks distinguish zero/identity mutations. References have NOT yet been
compiled/dispatched on a GPU. These newly authored definitions still require a
full historical semantic exposure audit and actual-tokenizer preflight before
being called fresh model tasks. No held-out confirmation tasks were created.
The task builder requires the full shared interface contract from the verifier;
the minimal test fixture is not sufficient for a real model experiment.

Run all local checks:

    node --test projects/reconfiguration/gain_reference_v1/test_*.mjs

At this revision, seventeen CPU/mocked-executor tests pass. They are not model
requests. Next: qualify reference shaders on an admitted GPU, pin model,
Doppler/runtime and verifier hashes, run exact tokenizer preflight, freeze the
selection inputs, then invoke the executor through the existing owned runner.

## Prospective native runtime

`../cross_domain_screen/native_runtime_v3.mjs` preserves the frozen v2 source
unchanged and records its source hash. V3 adds explicit reference capability
admission and paired capture. For same-pass runs, there is one original full
prefill, no deleted-instruction reference prefill, and GPU-derived per-layer gains
feed the existing decode/re-prefill paths. Shuffled controls recompute BOTH
instruction and complement energies from the shuffled full-prompt pass. Setup,
control and retained-cache costs remain in receipts. Reference A remains available
as its own named comparison.

Source locks for a new run must include v3, `capture_plan.mjs`, the new Doppler
paired kernel/wrapper/request, and their registry/generator identities. Existing
v2 source locks are not valid for v3. Exact-tokenizer qualification and service
guards are still required. The added runtime is syntax-checked; its model path
is unexecuted until hardware ownership and admission are resolved.

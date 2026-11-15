# Prospective channel-gain reference

Status: CPU reference qualification only. No model run, fresh quality result,
GPU integration, latency improvement or RSI is established by this directory.
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

The CPU tests qualify math and streaming capture only. A Doppler owner must
implement a GPU reduction of both spans from the same activation tensor, compare
it against this reference, and expose it through the existing channel-gain
request lifecycle. Do not read full activation rows back into the serving loop.
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

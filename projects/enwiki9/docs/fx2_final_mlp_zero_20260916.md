# One paid final-block capacity ablation

Candidate: `fx2_final_mlp_zero250k_v1`. Parent: original trimmed
`fx2_expert_release250k_v3` P, without the held lexical mutation.

The explicit lexical comparison closed validly with 13 archive bytes saved,
7 bytes over shifted control, unchanged executable size, and 433 additional
source ZIP bytes. Its source-component loss holds that candidate. The discovery
choice is a different, bounded question: does the final MLP earn its stored cost?

Deliberately combine lens 8 (measured tensor ablation) with the paid-object
perspective of lens 10. Exact original-weight preservation from lens 10 does
**not** apply: this experiment deliberately changes weights. The corpus codec
must still reconstruct every input byte. Novelty and a winning ratio are unproved.
The scope is one final block, not a layer-pruning or retraining sweep.

Other considered directions: lexical confirmation is held by its frozen source
cost gate; another final-output residual correction lacks a new measured signal;
truth-driven KV adaptation remains unimplemented and needs a defined update and
control. Neither is launched or declared scientifically disproved here.

## Fixed mutation and state boundary

Only `blocks.11.mlp.up.weight.q` (768 by 192) and
`blocks.11.mlp.down.weight.q` (192 by 768) become zero. Each has 147456 signed
weights. Keep tensor names, order, shapes, activation scales, row scales, all
other weights, generated RoPE tables, and the original container/loader.
In the container, symbol 7 represents signed zero. No runtime branch or new
option is introduced. The paid model file is generated before coding.

Source inspection of `TransformerOptImpl::step` shows that the last MLP follows
layer 11 attention and precedes only normalization/unembedding. The next step
reinitializes x from the decoded token and original PPMd prior; skip snapshots
are written only for layers below 6. Under identical decoded history and prior,
this last-block ablation has no route into subsequent neural KV/KDA state.
This is a source dependency argument, not a serialized native-state comparison.
Downstream mixer learning may change and is not required to remain parent-equal.

## Controls, evidence, and finite scope

P uses the original paid model. K canonical reserialization must reproduce that
model byte for byte; it therefore needs no duplicate native coding arm with the
same executable, model, command and input. D changes exactly the two matrices.
An independently compiled original native loader compares every expanded tensor,
requiring exactly those matrices to be zero and every other byte equal, including
regenerated RoPE. Missing targets, duplicate names, wrong shape and invalid
symbols fail closed. Synthetic tests precede model execution.

One exposed cold raw population [0,250000), 151210 modeled WRT bytes. Both P/D
receive clean repeated builds, full independent decoding, raw-derived repeated
encoding, full repeated exported neural streams and an untraced encode. P must
reproduce its retained 33429-byte archive and executable. No confirmation data
are read; a pass authorizes only unchanged independent 250KB confirmation.

Twenty-two outer phases: six preparation/loader operations plus sixteen native
build, preprocessing and codec operations. CPU2; memory 9999998976 bytes, swap0,
logical scratch 16000000000 bytes, aggregate stop 3600 seconds. Shared-host
execution timing is diagnostic. Resource failure is not a compression verdict.

## Decision and accounting

Let g = P archive minus D archive, z = D source ZIP minus P source ZIP,
m = D model minus P model. Require g >= 0, g-z > 0, m < 0, changed native neural
predictions, and every mandatory check for confirmation. This conservative
no-archive-regression screen is a search-budget decision, not a theorem that
all archive/model tradeoffs or larger populations fail. Report all measured
component totals even when that screen fails. Do not sweep layers or scales
in response to this result.

Report g-z, g-m and g-2m separately. The source ZIP already includes its model;
never add that model twice to the source form. Executable must be byte-identical
and added required options are zero. Preparation probes are disclosed research
tools, not runtime dependencies of the unchanged model loader. Complete package,
license, official options/multiplicity and full1G score remain unresolved. Do not
inherit earlier lossless weight-packing, lexical, trimming or teacher savings.

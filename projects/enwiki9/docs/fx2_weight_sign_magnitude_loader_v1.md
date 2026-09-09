# Direct sign/magnitude loading

Owner: `root_explore`. Source implementation identity:
`fx2_weight_sign_magnitude_loader_v1`. This implements the already measured
`GFX2SMG1` representation inside the authenticated adaptive FX2 loader and its
actual `OptModel::load` dispatcher. It preserves the sealed parents.

The [model receipt](../operations/provenance/fx2_weight_sign_magnitude_model_v1_terminal.json)
measured 416 fewer model bytes, exact original-model inversion and repeats.
The separate comparison executable adds 21,312 bytes, so that arrangement
does not pay. Direct integration must earn its actual binary and source cost.

The adapter stores magnitude counts at even leaves of the existing fifteen-leaf
histogram, with odd leaves zero. Its top three levels therefore have exactly
the same left and total counts as the eight-magnitude tree. The fourth level
is never decoded. A separate sign model is used only for nonzero magnitudes.
Both counts update after a complete weight; each rescales independently.
Existing canonical arithmetic replay, allocation limits and all older formats
remain supported. Production dispatch explicitly admits the new magic.

Source tests authenticate both parents, exercise exclusive output, reject
ambiguous patches and check deterministic materialization. They do not establish
native compilation, tensor equality, production probabilities or compression.

Next validation reuses the native tensor comparator and production dispatch
probe. Before execution, bind generated sources, build inputs, models, controls,
toolchain and resource bounds, publish ownership and verify fresh admission.
Test zero/nonzero signs, reset/rescaling, malformed/trailing input, every tensor
encoding and generated RoPE. Compare all initialized tensors and production
probabilities, then measure binary/source deltas against the adaptive parent.

With unchanged options, two model copies save 832 bytes. The runtime-pair delta
is `2 * (binary_delta - 416)`; the source-plus-decoder delta is
`binary_delta + source_delta - 832`. These are accounting formulas, not measured
package savings. No corpus launch or objective credit follows from source tests.

The [native unit receipt](../operations/provenance/fx2_weight_sign_magnitude_loader_unit_v1_terminal.json)
now records two native checker builds and seven passing tests from published
source `f1d979c69`. It confirms synthetic tensor parity, adaptive-parent
compatibility, mixed-sign rescaling and malformed-stream rejection. All26 input
bindings remain unchanged. Test fixtures were temporary; exact sources, test
logs and checker binaries are retained. This does not execute the production
dispatcher, initialize the trained model or measure production package cost.

The next [production gate](../operations/provenance/fx2_weight_sign_magnitude_production_v1_plan.json)
reuses the existing matched native build procedure after three full tensor
comparisons. It binds125 native source files, the comparator, runtime and helper
closure. The treatment uses GFX2SMG1; inherited runner labels are mapped explicitly
in its outer receipt. Three orchestration failure tests pass. Publication and
fresh admission precede execution; both incremental package alternatives must
pay before any separately frozen corpus test.

Published source `3e626e457` completed the
[production gate](../operations/provenance/fx2_weight_sign_magnitude_production_v1_terminal.json).
All434 initialized tensors and six104960-byte production probability/logit
outputs match exactly. The retained parent binary rebuilds identically; both
binaries are496136 bytes. The loader adds1576 raw source bytes and dispatch62.
Runtime-pair components save832 bytes, but raw-source-plus-decoder components
grow806 bytes. The frozen both-negative predicate fails; no corpus advancement.

The rules permit ZIP source and makefile as an executable alternative. The next
separate package realization will measure actual deterministic source/assets
ZIP bytes, extracted hashes and a relocated build. It must retain models,
dictionary, notices and options; raw-source and actual ZIP economics are distinct.
This preserves the negative result and grants no complete-package credit.

The [ZIP plan](../operations/provenance/fx2_weight_sign_magnitude_zip_v1_plan.json)
references the existing129-member dependency inventory and only three treatment
overrides. Both arms add identical quoted build/usage instructions. Five synthetic
tests pass for exact repeats/extraction, malformed membership and shared-manifest
resolution. Each relocated build executes the delivered build instruction.
The source ZIP contains one model, so its measured delta receives only one
additional decoder-side model delta; complete dependency qualifications remain open.

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

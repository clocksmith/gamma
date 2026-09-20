# Fixed P/E numerical attribution

The next experiment measures training-reference versus pinned native inference
without training or changing P/E checkpoints. Candidate
`fx2_numeric_attribution2048_q0_v1` is an analysis-only diagnostic, with zero
compression score credit. The complete-byte target remains 96,000,000.

The [frozen plan](../operations/provenance/fx2_numeric_attribution2048_q0_v1_plan.json)
and [experiment](../operations/adaptive/experiments/fx2_numeric_attribution2048_q0_v1.json)
bind the original native source, P/E model files, retained native input capture,
source closure, controls and stop conditions. The population is synthetic tokens
0..7 plus the first 2,048 retained native rows, preserving real reset markers.
Those are modeled-token rows, not raw corpus bytes. The real fixture overlaps
prior development exposure. No optimization or sample/checkpoint selection occurs.

For identical populations, report reference and native E-minus-P neural losses
and their difference, in bits. This measures the effect of evaluation semantics
on the checkpoint comparison; it is not a final-mixer or archive measurement.
Native and reference observers must each preserve their unobserved output exactly.
Decoded weights/scales must agree byte-for-byte across the native loader, packed
container decoder and checkpoint export. Checkpoint tensors remain unchanged.

Trace the first 64 input rows and apply separately at most three first-difference
native vector substitutions and eight integer-coordinate substitutions, always
replaying the full unchanged fixture. Residual differences remain explicit.
Native intermediate substitutions are diagnostic interventions only.

[Synthetic preflight](../operations/provenance/fx2_numeric_synthetic_preflight_20260919.json)
finds P's block-3 MLP-down bin divergence and E's block-10 forget-gate-up bin
divergence. One integer substitution per checkpoint removes remaining inspected
integer differences on eight tokens, reducing maximum logit gaps to 0.00000572
and 0.00000477 respectively. Floating residuals remain. Both implementations
find E worse on those seven scored positions; the mismatch changes E-minus-P
loss by -1.1301946 bits. This does not establish the real-input result.

Job `20260920T023220Z_bded1a9e05` is queued under owner
`codex-numeric-attribution-20260919`: CPU 3, 4,000,000,000 resident bytes,
1,500,000,000 scratch bytes, no swap, 1,800-second wall stop. Timing is diagnostic.
Before launch, publish the source, ownership and frozen inputs. After completion,
retain the exact comparison, first-divergence evidence, reflection and canonical
run row, then update this report with measured conclusions.

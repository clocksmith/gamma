# Exact magnitude and shared-sign packing

Owner `root_explore` tests one exact representation against the adaptive FX2
model packer. [Frozen synthetic contract](../operations/adaptive/experiments/fx2_weight_sign_magnitude_v1.json).
The decoder reconstructs each signed weight from magnitude and a shared sign
distribution. No trained parameter changes and no approximate inference occur.

The new assumption is that sign statistics can be shared across magnitudes
within a tensor. This can reduce statistical overhead, or lose when sign and
magnitude are dependent. Existing neighbor and width-carry losses remain intact.
Magnitude/sign trees use the unchanged Q11 range coder at depths three and one.
Zero has no sign. Both count rows update only after a complete weight and reset
per tensor. Their initial joint prior is uniform before probability rounding;
the different tree does not promise rounded-probability identity with the parent.

The source adapter authenticates its parent and emits a distinct header, format
magic and inverse. All metadata and non-INT4 bytes follow the unchanged format.
Separate P/K/D processes must reconstruct the original container and repeat it.
State witnesses contain every pre-weight magnitude/sign count and total, encoded
as twelve little-endian uint32 values followed by the exact offset weight symbol.
Use tracing for original-input D encode or D-input restore. D-input D-output
would concatenate both directions and is not a framed comparison trace.
K follows new bookkeeping source but emits the exact P archive; optimized-away
work is not measured or claimed as a runtime control. D encoder/decoder state
agreement is the authoritative count-synchronization check.

The prospective execution manifest extends the frozen contract with the complete
phase-helper import closure and independent exact Q11-vector fixtures. Verify
the union before and after execution. Synthetic correctness permits preparing
one separately published complete-model comparison; it gives no trained-model,
archive, integrated-package or full-corpus score credit. A comparison executable
is not an estimate of the native loader's added bytes.

# Native value-feedback preflight

The selected quantizer now executes inside the existing native transformer.
This is synthetic integration evidence, not an arithmetic archive experiment.
It leaves the live `fx2_trim_scale10m_v1` source and process unchanged.

The materializer verifies the immutable trimmed model source and kernel hashes.
P is the exact delivered source. K/D/S add one header and change only
`cpp_infer/src/opt/model_opt.cpp`. All three have 576 int32 residuals, reset by
`begin_article`. Before updating a layer, they copy its previous residuals so
the shifted control cannot accidentally consume current-token state. K retains
the original int8 values; D applies aligned feedback; S borrows the previous
residual from the next coordinate within the same head. Existing weights, Q/K
quantization, cache geometry and learning code are preserved. D/S are expected
to change later neural and mixer states; they do not promise parent parameter
identity after changed predictions.

Seven native tests passed using the authenticated GCC 15 compiler and existing
transformer flags. Four arms process a fixed synthetic 1,088-token sequence,
crossing the 1,024-token cache window. Independent repeats and 64-token prefixes
are compared byte for byte. Every invocation then resets the already-used model
and reproduces its first 64 probability rows. An uninstrumented D build also
matches the instrumented D stream exactly.

Observed P/K FP32 probabilities are identical. D differs from P and S. All
probability rows are finite and normalized. Observer assertions verify every
quantizer input/output conservation identity, residual bound, previous-token
donor coordinate and reset. Full parent/optimizer state is not serialized;
these observations do not replace the forthcoming coder and inverse checks.

The preflight covers 10,880 native model steps. It consumes no corpus and
produces no arithmetic archive. The first harness attempt failed at compiler
identity lookup: it selected Clang although the retained native profile uses
GCC. It reached neither compilation nor inference. That failure and its source
snapshot are retained; only the test harness compiler selection was corrected.
No quantizer parameter or model realization changed.

The regenerated P source ZIP matches the immutable parent exactly. Each K/D/S
ZIP is 3,906,718 bytes, compared with P's 3,905,220: an additional **1,498 source
component bytes per counted copy**. This includes the existing paid model and
dictionary in both packages. There is no additional coefficient table. The
2,304 residual-state bytes are runtime memory, not transmitted data. Executable
delta, complete runtime closure, official packaging multiplicities, and full
score remain unknown. Source and binary alternatives must not be added together.

The next discriminator is one separately frozen native P/K/D/S comparison on
the exposed opening 250KB, with unchanged parameters. Require final coder
probability/interval parity for P/K, each arm's exact independent inverse and
repeat, observer-off identity, residual synchronization, and actual archive
and package differences. A positive result must then face unchanged reserved
data. No larger corpus result is implied by the weighted rounding-error bound.
Do not launch beside the present 10MB job without an admitted aggregate scratch
budget; the current independent work is synthetic development only.

The component's intent and boundaries are unchanged. The 90,000,000 complete-byte
objective remains unproved.

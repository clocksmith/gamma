# Native test of the trimmed auxiliary package

Candidate `fx2_trim_auxiliary_ppm_v1` tests the separate
[packaging repair](fx2_trim_auxiliary_ppm_20260916.md). The comparator is the
original 3,910,568-byte source ZIP. The treatment is the already materialized
3,907,353-byte repaired ZIP. Neither is the held value-feedback treatment.

The question is whether removing the neural fallback and using PPM-only coding
for the fixed auxiliary assets produces a functional, smaller set of native
components while preserving the same main transformer archive. The expected
gain is unknown; larger auxiliary streams may consume the executable saving.

## Frozen population and execution

Both arms retain the exact 411,996-byte dictionary, 1,094,862-byte article-order
table and 2,930,652-byte trained model. The main-path check uses the exposed cold
raw interval `[0,250000)` and its retained 33,429-byte native reference. This is
not a previously unseen confirmation population and does not run the complete
split/PHDA/reorder corpus pipeline.

P uses the original auxiliary codec. D uses the delivered PPM-only packager.
Each arm clean-builds twice, compresses/decompresses/repeats both fixed assets,
and encodes/decodes/repeats the main sample. All restored bytes, repeated assets,
and main archives must match their exact references. There is no predictive
parameter fit or backend sweep.

The gate has 29 outer subprocess phases, including one delivered-packager
phase containing four child codec invocations. It retains those four child
commands and return codes. CPU 2, memory 9,999,998,976 bytes, zero swap, logical
scratch 16,000,000,000 bytes and a 7,200-second aggregate stop bound execution.
Per-phase stops are explicit in the runner. Timing is shared-host diagnostic.
It stays held behind the current trimming and value-feedback execution order.

## Real embedded extraction, separately identified fixture

A test executable includes the arm's exact `self_extract.h` and calls its
compressor/decompressor extraction functions. Their subprocesses execute the
actual compiled native compressor with its appended assets. The fixture does
not replace those subprocesses with a mock during the native gate.

Each extraction starts inside an otherwise empty Bubblewrap filesystem. It
contains one assembled container, the extraction fixture, `/bin/sh`, the five
declared ELF runtime files, and scratch. It has no repository, external model,
dictionary, order table, full `/usr`, or network. Exact asset hashes are checked
after extraction. A separate restricted native decode then reconstructs the
main sample using only the dictionary, weights and payload obtained from the
container.

The decoder container's payload is the native opening-prefix archive. Its
extraction is an explicit bootstrap fixture, not an official enwik9 submission
or a successful invocation of the full argumentless reconstruction pipeline.

Four synthetic tests already exercise the actual header extraction and sandbox
wiring. Those tests deliberately use an ELF copy stub in place of the codec;
their synthetic asset streams are not compressed. They prove helper invocation,
layout, dictionary rejection and host-file isolation, **not PPM correctness**.
The admitted native gate supplies that missing evidence.

## Accounting and decisions

Let `B` be the rebuilt executable, `D` the compressed dictionary, `O` the
compressed order table, `W` the model and `A` the native sample archive. The
assembled compressor has `B+D+O+W+16` bytes. The decoder bootstrap fixture has
`B+D+W+A+16` bytes. Both byte counts are measured from actual files.

Two diagnostic component comparisons are reported separately:

* Assembled compressor plus decoder fixture.
* Delivered source ZIP plus decoder fixture.

For each, compute the P total minus the D total. These are alternative component
forms; their savings are never summed. Required invocation/build options,
licensing, target-platform treatment and the full-corpus pipeline remain
unresolved. The actual assembly includes the model and dictionary; they are
not counted as free. No published external score is inherited.

All required inverses, repeats, source/runtime identities, main archive parity,
guards and cleanup must pass before economic interpretation. A positive
component comparison retains this package realization for subsequent integrated
qualification. Nonpositive comparisons close this realization's paying-package
claim at the tested component boundary. A correctness, resource or evidence
failure leaves the comparison incomplete. No automatic larger or full-1G run
is authorized; the 90,000,000-byte complete target remains unproved.

# Frozen native value-feedback comparison

Candidate `fx2_value_feedback250k_v1` evaluates one already selected realization:
Q16 error feedback on all three native attention-value layers, using the parent
int8 cache and existing trained weights. It does not change coefficient strength,
layer selection, cache length, parameter precision, mixer learning rules, or
online update schedule. The original parent learning values may change in D/S
because the predictions change; this is an intentional trajectory mutation.

Use the authenticated trimmed release P on the exposed cold opening raw
`[0,250000)`. The frontend gives 151,210 modeled bytes and 1,209,680 bit events.
No confirmation data is consumed. The native synthetic preflight and local
weighted-error theorem justify this test, but provide no compression credit.

| Arm | Definition |
| --- | --- |
| P | Unchanged, byte-identical trimmed source and executable. |
| K | Feedback bookkeeping executes; original quantized values drive the model. |
| D | Apply the aligned previous-token residual at each value coordinate. |
| S | Same computation and state, but use the next coordinate's previous-token residual within each head. |

Each arm receives clean-source compilation and recompilation, a delivered
encode and independent delivered decode, then an observed encode, independent
decode, and reencode from restored raw input. P additionally verifies the
retained frontend and 33,429-byte native archive. The four arms comprise 44
subprocess phases: 12 builds, 11 cleans, one preprocessing check and 20 codec
operations. There is no hidden parent-probability input or teacher.

The observed builds record every final coder float probability, integer count,
interval and truth bit. K's records and archive must equal P byte for byte.
Each observed arm's encoding, decoding and repeat records must match; their
archives must equal the corresponding delivered build. K/D/S also record every
feedback residual and reset, with runtime assertions on visit order, donor
state, conservation and the bounded residual. These streams must match exactly
across encode/decode/repeat. Full parent and optimizer memory is not serialized;
the contract does not claim that observation.

After exact residual comparisons, retain one complete copy per arm as ordered
zlib chunks, each with at most 8MiB uncompressed bytes. Every chunk is decoded
and compared before the repeated raw files are removed. The manifest binds both
raw and stored hashes, lengths and order. This is evidence storage, not a codec
change or compression gain. Partial failed evidence is preserved.

Report `g_P=P-D`, `g_S=S-D`, delivered source-ZIP delta and executable delta.
The selected source increment is 1,498 bytes; the binary increment is measured
by this gate. These are alternative component-accounting forms. Required models,
dictionary and invocation stay present. Complete official packaging, runtime
closure, multiplicities, and full-corpus score remain unknown.

Strictly positive `g_P` and `g_S`, all required checks, and a component increment
at most 65,536 bytes authorize **one unchanged same-size confirmation**, not
a larger run or prize claim. Use the existing reserved raw
`[500000000,500250000)` population without selecting among slices. It is
historically exposed to other mechanisms and untested by this one. Source and
binary component net values remain visible even when negative; a fixed package
cost is not paid afresh per sample. Full-package economics must pass before
large-scale promotion. A valid non-improvement retires this configuration, not
all quantization methods. Correctness, trace, resource or evidence failures
remain distinct from compression rejection. No parameter rescue follows.

The prospective native envelope is CPU2, 9,999,998,976 memory bytes, zero swap,
20,000,000,000 logical scratch bytes and a 7,200-second aggregate stop. Codec
operations stop at 300 seconds, builds at 360, cleans at 30, preprocessing at
180. These are execution limits, not work estimates. Retained PPM scratch
requires about 14.68GB logical space; observation streams are included. Do not
start beside the active 10MB gate without aggregate resource admission. Publish
held ownership first, and preserve the live gate and its observer unchanged.

The target remains exact canonical enwik9 with at most 90,000,000 complete bytes.
This gate can establish a local native mutation, not that final witness.

# MOBIUS-2 NOEMA causal and canonical replay contract

Date: 2026-08-01

Status: canonical requirements for any NOEMA successor after
`mobius2_noema_binary_carry_headroom_qh0_v1`

## Evidence boundary

MOBIUS-2 currently has zero score and forecast credit. Route E single-page
prototypes, ordered-template surface LOGOS, cross-page lexical-frame LOGOS, and
the equal-span binary-carry NOEMA QH0 are terminal concrete constructions. Their
results do not invalidate the general state-preserving bypass principle or a
materially broader semantic LOGOS universe. The planning forecast remains
109,389,323 bytes until a counted native replay changes it.

This contract prevents a future hierarchy result from depending on current-byte
leakage, reversed chronology, stale checkpoint state, an unfair control,
future-truth rotation, in-memory weights that differ from the paid model, or an
incomplete GPU preflight.

## Byte-causal frontier

Before byte `x_t`, the hierarchy frontier must cover exactly `x_[0,t)`. The
current byte cannot become a leaf until all eight truth bits are decoded:

```text
predict byte t from summaries of completed bytes [0,t)
for bit b in 0..7:
    combine exact Gamma P1 with the frozen NOEMA frontier
    select the binary-prefix output using only decoded bits [0,b)
    decode truth bit b
after bit 7:
    create Leaf(x_t)
    perform ordered carries
expose the new frontier first at byte t+1
```

Every merge is ordered as:

```text
Merge(older_left_span, newer_right_span, level)
```

Child order is part of the model even when the learned transition appears
approximately symmetric.

After every completed byte, occupied intervals must be ordered, nonoverlapping,
and cover the completed prefix exactly. An occupied level `l` represents exactly
`2^l` bytes. For an uninterrupted `N`-byte tree, the merge count is:

```text
N - popcount(N)
```

With resets, the receipt records the sum over reset regions. A 128-byte patch
therefore performs 127 merges; the retired QH0 population of 4,540 complete
patches implies 576,580 merges. A future executable checker must also perturb
the current and future bytes and prove that earlier frontier outputs do not
change.

## Checkpoint replay and selection

Every checkpoint owns the states produced by its merge cell. For each candidate
checkpoint:

1. Load only that canonical checkpoint.
2. Reset at the declared boundary.
3. Replay every required completed predecessor byte with that checkpoint.
4. Score only the selection population.
5. Destroy the state before evaluating another checkpoint.

State produced by the final epoch may not score an earlier checkpoint. When
state persists across pages, replay begins at the corpus or declared reset
boundary, not at the first scored page.

Future selection minimizes exact two-part selection cost:

```text
selection_payload_j + selection_raw_bytes / 1,000,000,000 * package_j
```

Exact ties choose the earliest checkpoint. The selected checkpoint alone opens
sealed confirmation. The retired QH0 historically selected minimum payload
because that rule was frozen before this successor contract; it failed even
without the additional package term.

## Matched controls

The flat control and hierarchy share input bytes, binary-prefix head, training
pages, optimizer schedule, checkpoint count, quantization, serialization,
package accounting, exact range coder, current-byte prefix visibility, and
reset boundaries. The intended difference is only:

```text
flat:      one chronological recurrent state
hierarchy: recursively merged equal-span summaries
```

The aligned-hierarchy null must not be advantaged or invalidated by future
truth. A future promotion control uses a frozen positive page lag or a
deterministic hash-selected earlier page. A future-derived page rotation may be
reported only as a nonconstructive specificity diagnostic and may not satisfy a
promotion inequality. The retired QH0's NS is preserved under that diagnostic
label; its decisive negative selection, sealed magnitude, and loss to N1 do not
depend on NS.

## Two-layer exact replay

Parent identity records:

```text
parent payload byte identity and SHA-256
decoded WRT SHA-256
official restored-raw SHA-256
```

After checkpoint selection, candidate identity must:

1. Serialize the selected model canonically.
2. Destroy the training object.
3. Parse and reload only the serialized bytes.
4. Generate the complete adjusted legal P1 stream.
5. Encode and decode the complete arithmetic payload.
6. Reconstruct WRT and run the official inverse.
7. Repeat the model-to-P1-to-payload procedure independently.

Canonical model, adjusted P1, candidate payload, decoded WRT, and restored raw
hashes must repeat exactly. Independently terminated development, selection,
and sealed streams are economic diagnostics; only the complete stream is the
identity certificate. Each split states whether model state resets or is
replayed through unscored predecessors.

## Canonical package

The model format binds magic, schema version, architecture identifier, tensor
count, fixed tensor IDs or sorted names, dimensions, quantization type,
little-endian scales, raw quantized values, lookup tables, and an internal
checksum. The decision model must be parsed from this blob rather than passed
through an in-memory dequantized dictionary. Filesystem metadata, Python
dictionary order, and `.npz` behavior are outside the format.

Same-host ROCm float or dequantized execution remains zero-credit headroom
evidence. A deterministic integer or dyadic runtime is authorized only after a
target-bearing hierarchy survives the frozen gates.

## ROCm proof receipt

Preflight records `sys.executable`, PyTorch version, HIP runtime version, device
name, device architecture, visible-device count, training dtype, matrix input
hashes, matrix output hash, and explicit synchronization. The matrix remains on
the GPU until synchronization and checksum extraction. Visibility without
executed compute is not a launch certificate.

## Frozen economics

For exact sealed parent bytes `B0`, candidate bytes `BN`, represented raw bytes
`RH`, and complete package `PN`:

```text
gross_BPM = (B0 - BN) * 1,000,000 / RH
net_BPM   = gross_BPM - PN / 1,000
```

One package is amortized over the one thousand raw megabytes in `enwik9`.
Authorization requires exact parent and candidate identity, legal nonzero
probabilities, explicit package accounting, positive development and selection,
at least 3,000 sealed gross B/M, at least 2,100 sealed projected net B/M, and a
strict total win over the matched flat and causal misalignment controls.

Both scientific authorization and rejection return process status zero.
Nonzero status is reserved for malformed experiments: missing inputs, broken
identity, nondeterminism, illegal probabilities, inverse failure, or runtime
failure. Oracle scaffolds remain explicitly queued, heavy-lock-respecting jobs
outside ordinary compressor discovery until a constructive codec exists.

## Successor interpretation

A pass authorizes only the preregistered distant replay. A second pass authorizes
integer compilation and evaluation of whether the hierarchy can replace Gamma
work rather than only add an endpoint. High-density NOEMA-over-Gamma residual
spans may then seed residual-directed semantic LOGOS concept discovery.

A failure retires the exact topology, widths, reset policy, optimizer,
checkpoint schedule, and quantization without rescue sweeps. A successor must
change the information source. The remaining major MOBIUS direction is a
broader semantic LOGOS zero-cost or lower-bound grammar ceiling that clears
3,000 B/M before rules, slots, surfaces, and source are paid.

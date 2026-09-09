# Compact previous-word implementation

Owner `root_explore`; independent tests `next_prediction_gate_review` and source
review `direction_certificate_review`. This is a new implementation identity.
The [measured predecessor](../operations/provenance/opcode_previous_word_terminal_20260909.json)
saves147 development archive bytes but its adapter source costs1277 extra bytes.
The [ZIP measurement](../operations/provenance/opcode_previous_word_source_zip_20260909.json)
also fails the scoped archive-plus-source comparison. Preserve both results.

The [builder](../tools/opcode_previous_word_compact_build_v1.py) authenticates the
compact parent's packed source, integrates the same history and literal key,
and produces one packed source plus its loader. It changes no coding mechanism.
P uses parent keys without tracked histories; K tracks without injection;
D and S select the same immediate and delayed words as the predecessor.
The prefix-cost estimator creates a state with history disabled, so it retains
the parent's literal keys without temporary global mutation. The active arm is
an immutable namespace input. Decoder framing and malformed-input guards remain.

Synthetic acceptance requires same-arm archive and complete observation parity
against the measured predecessor, independent inverses/repeats, unchanged prefix
costs, exact history updates across copied bytes, namespace isolation, malformed
input rejection, deterministic materialization and refusal to overwrite.
Use at most six fixtures, at most4096 aggregate raw bytes, CPU3,512MiB address
space,120 CPU seconds,180 elapsed seconds and32MiB per output file. These are
test bounds, not an engineering estimate or corpus-launch authorization.

Measure local source bytes separately from complete runtime and submission
accounting. No source-size reduction earns inherited corpus savings before
observed corpus parity. Any fresh population needs its own frozen admission.

The [six-test synthetic receipt](../operations/provenance/opcode_previous_word_compact_unit_20260909.json)
retains352 artifacts in one verified ZIP. All four arms match the predecessor's
archives and complete witnesses on six fixtures totaling1173 raw bytes. The
local bundle is5961 bytes,1062 below the adapter and215 above the original parent.
This result leads to a separate [treatment release](opcode_previous_word_release_v1.md).

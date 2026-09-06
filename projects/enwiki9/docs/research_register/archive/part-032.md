# Research Register Archive - part 032

[Current register](../../research_register.md) | [Register index](../README.md) | [Archive index](README.md)

## 2026-09-05 - Native MIDAS coder and causal scheduler pass synthetic checks

`lib/midas_native_codec.hpp` provides native finite Q16 arithmetic encoding and
decoding, explicit raw-byte identity framing, a pre-truth byte-to-bit adapter,
complete coder checkpoints and an exact first-state-divergence comparison.
`lib/midas_midpoint_schedule.hpp` provides the P/K/F/S update boundary: ordinary
parent updates after each 64 decoded bytes, an additional F update after the
first 32, and S with those already decoded targets cyclically shifted left once.
Every update rebuilds the active prefix from its retained segment origin. K
executes update and rebuild on a discarded copy, preserving the authoritative
parent. These are reusable components, not a sealed corpus candidate.

Three targeted tests pass with strict C++17 compilation. Separate address and
undefined-behavior sanitizer executions also pass. The native counting-fixture
payload equals the independently implemented Python payload; finite inverses,
repeats, corruption rejection, checkpoint continuation, P/K probability and
payload identity, and encoder/decoder state synchronization pass on synthetic
fixtures. The scheduler's sentinel deliberately invalidates recurrent state at
update, so prediction without rebuilding fails. These fixtures do not implement
or prove a neural predictor, complete-model gradients, or a MIDAS gain.

Evidence: `operations/evidence/20260905_midas_native_codec_scheduler_unit_validation.json`
binds source SHA-256 values, test commands, compiler identity and observed output.
Score credit is zero. The standalone trainable parent roundtrip remains missing.
No corpus experiment was launched and no partial HORIZON science was read.

The concurrent unregistered `programs/compact_midas_open_parent_q0_v1` source
tree was left untouched. Coordinate its owner before integrating the one compact
challenger: validate full gradients and optimizer/recurrent state, measure its
dominant kernel, and prospectively freeze the bounded parent P/K/F/S archive
gate. An independent eligible-parent explorer must preserve that ownership and
HORIZON's sole observer, retain source/package/resource bindings, and produce
exact finite archives without inheriting compression claims from a teacher.

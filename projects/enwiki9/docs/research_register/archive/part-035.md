# Research Register Archive - part 035

[Current register](../../research_register.md) | [Register index](../README.md) | [Archive index](README.md)

## 2026-09-05 - Real open MIDAS parent passes a bounded native roundtrip

`lib/midas_open_profile_fixture.hpp` connects the existing Gamma open neural
forward, complete backward and full optimizer update kernels to the new native
coder and P/K/F/S scheduler. It does not call the legacy replay's differently
defined K/S dispatcher and does not consume LibNC or pretrained tensors. The
integration fixture has one 64-feature layer, an eight-unit feedforward inner
dimension, eight memory positions, a 256-byte vocabulary and fixed initialization.
This is not a selected competitive architecture or a corpus candidate.

All four arms encode 65 synthetic bytes into 105-byte finite framed archives,
invert exactly, and re-encode identically. P/K probabilities, archives and
authoritative predictive-state projections match. K's discarded real full update
and rebuild matches F's midpoint backend byte-for-byte. F visits all 18 declared
parameter tensors and changes 15, including embedding, attention, feedforward and
output weights; S produces a different full-model midpoint state. Every arm shares
the full 64-byte parent update; F/S add the causal 32-byte midpoint update. This
schedule is not claimed to inherit the old teacher replay's compression behavior.

Six regression tests pass. The separate address/undefined-behavior sanitizer
build also passes and produces the same four archives. Pending and boundary
checkpoints match across encoder and decoder; corrupted tensors, negative second
moments and mismatched cached probabilities are rejected. A separate process
decodes an additional fixture after its source file is removed.

Evidence: `operations/evidence/20260905_midas_open_profile_parent_roundtrip_unit.json`
retains raw and archive bytes as hex, SHA-256 values, source bindings, the build
recipe, validation output and bounded encode/decode CPU/RSS observations. This
closes a synthetic inversion and synchronization gate, not a compression-gain,
gradient-reference, complete-package, resource-qualification or full-corpus gate.
No compression gain or objective credit is awarded.

The reference recomputes all 64 graph states for every byte. Before any corpus
successor, coordinate the compact-parent owner, bind an incremental pre-truth
forward implementation against this reference, and select the architecture under
explicit kernel, package, memory and runtime budgets. The other agent's candidate
tree and HORIZON remain unchanged. This session's requested `rdpull gamma` still
fails SSH public-key authentication; local and concurrent work was preserved.

## 2026-09-05 - Join the native MIDAS bit boundary and checkpoint state

`lib/midas_bit_predictor.hpp` now connects the causal midpoint scheduler and
byte adapter behind one pre-truth `predict()` / `observe(decoded_bit)` interface.
Combined checkpoint restore rejects inconsistent byte/bit clocks, mismatched
pending-byte ownership, differing pre-truth distributions, excess checkpoint
size, truncation and trailing bytes. All P/K/F/S finite sentinel inverses and
repeats pass through this interface with exact predictor and normalized coder
state agreement. P/K probabilities, payloads and authoritative-state projections
remain identical. Three regression tests and the joined address/undefined-behavior
sanitizer fixture pass.

Evidence: `operations/evidence/20260905_midas_bit_predictor_join_validation.json`.
This is implementation correctness only, with zero score credit and no corpus
access. A real complete-update trainable backend and its parent roundtrip remain
missing; the other owner's compact predictor source was not changed. The prior
source-bound infrastructure receipt remains unchanged and resolves at local
commit `9d327137`.

The user's `rdpush gamma` request created that commit but could not publish:
GitHub rejected SSH public-key authentication and the agent had no loaded
identities. No credential configuration was changed. Authentication must be
restored before publishing these local commits. HORIZON and its sole observer
remain unchanged, without partial scientific access.

# Research Register Archive - part 039

[Current register](../../research_register.md) | [Register index](../README.md) | [Archive index](README.md)

## 2026-09-06 - MIDAS boundary observability passes exact synthetic checks

The [new observer](../../midas_open_boundary_observer_v1.md) wraps the unchanged native
MIDAS codec and records every pre-truth probability plus complete serialized
state at initialization, every 32 decoded bytes, and finalization. All five
[synthetic regression tests](../../../operations/evidence/20260906_midas_open_boundary_observer_unit.json)
pass on CPU2. P/K/F/S preserve the retained 105-byte archives of the 65-byte
fixture; each independent decoder and repeat matches every probability,
boundary record, complete state and exact snapshot. An independent parser
checks all 17 component ranges, and identical malformed bundles cannot pass.

The 432,528-byte observer executable and all 532 compiler dependencies are
hash-bound. The aggregate guard passes and its cgroup is removed. This supplies
observability code, not a corpus certificate or package qualification. The
existing opening250KB gain remains held until a separately frozen successor
measures these boundaries on corpus data. No measured MIDAS source changed.

## 2026-09-06 - Schema transfer is exact but every block falls back

The [terminal audit](../../../operations/provenance/wiki_schema_exact_transfer250k_terminal_20260906.json)
closes all 24 phases of `wiki_schema_exact_transfer250k_q0_v2`. All P/L/D/C arms
produce 111,159 bytes on opening250KB and 106,139 bytes on distant250KB; all eight
inverses and repeats pass. ROOT independently reconstructs every baseline block
and verifies its framing, hash, and exact accounting. Serialized dictionaries
agree at all 62 block boundaries across every arm and phase.

D proposes 454 opening and 337 distant references, but no grammar block is
selected. Even the cheapest proposal exceeds its baseline by 168 opening bits
or 88 distant bits. Archive saving is zero and selected C associations are
inactive, leaving causal attribution inconclusive. This evidence concerns the
tested cold-population realization and does not disprove grammatical structure.

The [canonical decision](../../../results/wiki_schema_exact_transfer250k_q0_v2/decision.json)
binds all 142 other required outputs. Its frozen aggregate rules yield both
promotion and kill false, hence `retry`; the [validated reflection](../../../operations/adaptive/reflections/20260906T023145Z_eb44974e5c.json)
holds work without an automatic rerun or 1M gate. Eight canonical ledger rows
preserve unknown complete-package and full-score values.

# Amendment 1, 2026-10-23: full successor rule (before launch)

Codex's review (gamma-team LOG, 19:43Z) found that item 14's successor checks also include full readiness against
the original control. This audit's successor rule omitted it. Nothing has run.

**Change.** Under every pairing, each successor comparison now adds a `ready_vs_control` conjunct: the full
input-candidate rule against `coupled_control256`, under the same encoder pairing. `contract.json` names that
comparator as `ready_comparator` for both successor comparisons. The expected historical failures are unchanged:
the fraction predicate only, since both arms are recorded as ready against the control.

**Wording.** In FREEZE.md Q2, the rationale is only a prediction. segmentation-audit-v1's lack of tie headroom on
control128 does not bound the tie headroom of compiler joint128.

**Launch.** A single process with a 600 s timeout.

`audit.py` hash changes from `c7b7f8970d4cfd59b2f79da2676ce0dec8d54bbd64a000a5586767a88dbf7639` to `f66793a45c6c44e0e04833119db0ae409d1e78139ded74a73c6c743a3786eee0`. This file is added to
the contract.

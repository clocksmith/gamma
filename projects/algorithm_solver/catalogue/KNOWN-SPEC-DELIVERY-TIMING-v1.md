# Exact known-spec artifact delivery: bounded native measurement

This is a component measurement toward goal 1c, **not full 1c qualification**.
The native dot Python 3.13.5 process validated the pinned catalogue/receipt
bindings, then traversed every currently qualified language artifact once.
Each request retained the normal authorization, protected-ID gate, anchored
no-follow filesystem access and exact source-byte hash verification.

- Full metadata universe: 4,081 IDs; 166 known protected IDs remain closed.
- Artifacts delivered: 400 JavaScript and 378 Python, zero failures.
- Total source bytes verified: 228,287; source bodies are not in the receipt.
- Initialization: 166 ms. Whole traversal: 722 ms.
- JavaScript request median/p95: 0.593 / 0.810 ms.
- Python request median/p95: 0.586 / 0.779 ms.

These are one sequential traversal, not repeated-trial confidence intervals or
cold-cache results. OS cache state was uncontrolled. Description encoding,
recognition, query-public correctness checking and candidate execution were
not included; no execution or end-to-end latency gate is claimed. The exact
configuration, delivered-identity digest and Python executable identity are in
`KNOWN-SPEC-DELIVERY-TIMING-v1.json`. Historical M1 remains unmet.

`benchmark_known_spec.py` refuses a traversal exceeding its request cap rather
than silently selecting an easier subset. It emits aggregate timing/identity
metadata only. Its operator-supplied configuration remains a trust boundary.

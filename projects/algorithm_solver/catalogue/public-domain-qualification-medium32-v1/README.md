# Medium32 first-wave qualification and integration

Status: completed and independently adopted. Sixteen sources pass13,898 checks
in444 isolated calls; all944 catalogue artifacts read back through live gates
in the linked v16 service. See `QUALIFICATION-RESULT-v1.json`,
`ADOPTION-AUTHORITY-v1.json`, and `SERVICE-INTEGRATION-v1.json`.
Finite typed/local-effect qualification is not universal proof or M1 completion.

Exact first8
IDs:1248,1319,1338,1400,1466,1471,1482,1540. Full32 worklist is preserved in
`worklist.json`; remaining24 sources have not been opened by this lane.

See [PLAN.md](PLAN.md), [contracts.json](contracts.json), and `semantics/` for
explicit official-domain, local-effect, source-provenance and resource boundaries.
Original owner sources remain unchanged; no canonical registry claim was made.

Host-only controls: `/usr/bin/python3 -m unittest test_foundation -v`.
`qualify.py prepare` freezes a reviewed-input candidate without executing it.
`run` requires independent/root-authorized exact-freeze review, uses only the
approved native judge, and never automatically adopts sources. `verify.py`
recomputes every typed/effect verdict from the frozen host oracle and raw outputs.

# Medium32 wave2: completed with a resource failure

The original sixteen-source run passes15 sources and21,240/21,272 checks.
JavaScript1743 exhausts the unchanged64MiB Node heap on the batch containing
the public100,000-vertex path fixture. Python1743 and the other14 sources pass.
This is a resource failure, not proof of semantic incorrectness. No cases are
dropped or limits raised. No adoption is represented by this checkpoint.
`QUALIFICATION-RESULT-v1.json` preserves the exact original result; any repaired
source requires a separate freeze and matched full replay.

## Preserved preparation scope

Originally prepared before independent review and execution. This linked second wave covers eight
IDs /16 source-language pairs; `worklist.json` preserves the complete32 IDs.
Wave1 and incoming owner sources remain unchanged.

[PLAN.md](PLAN.md), [contracts.json](contracts.json) and `semantics/` record the
public official domains, local effects, independent oracles, provenance and caps.
Run host-only controls with `/usr/bin/python3 -m unittest test_foundation -v`.
`qualify.py prepare` does not execute candidates; `run` requires a separately
reviewed frozen contract and uses only the approved native judge. `verify.py`
rechecks every raw observation. No canonical claims or adoption happen here.

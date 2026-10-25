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

## Completed partial original-source adoption (v18)

The original16-pair run completed with15 passing pairs and one resource failure: JS1743 passed174/206 cases, with the32-case batch at offset128 exhausting the64MiB Node heap. No failing case was removed, cap increased or semantic incorrectness inferred. The15 passing **original-source** pairs were independently replayed and adopted in v18; `SERVICE-INTEGRATION-v1.json` binds the actual status (486JS/487Python at that stage). JS1743 remains authored and unqualified, not silently absent from the denominator.

The [packed-source successor](../public-domain-qualification-medium32-wave2-memory-v1/README.md) also failed the same batch. Its separate negative evidence is preserved; it did not qualify JS1743 and was not substituted for the adopted original sources. `ADOPTION-AUTHORITY-v1.json` is an exact copy of the reviewed operator authority; source payloads and private catalogue records are not copied here.

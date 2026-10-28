# S20 controller repair: refetched response hash recorded, not pinned

Derived from [the byte-preserved v1 controller](../continuation-s-qualification-20261028-v1/README.md). Everything else in v1 is unchanged: selection, source manifest, observer profile, source and observer reviews, plan, required-domain accounting for 208, limits, run and replay.

## Why

On 2026-10-28, `prepare` on the Linux executor failed for all ten problems with `exact official definition/API/language template drift`. Checked field by field, every problem still matched its pinned content hash, official API and the Python and JavaScript template hashes. Only the hash of the whole response differed. The definition query returns templates for every language, so a change to any unselected language's template changes the raw response hash without changing anything this lane executes or compares.

## Change

`definitions()` no longer requires the refetched raw response to equal `official_definition_sha256`. Question identity, slug, free-access status, content hash, official API and both selected template hashes remain exact requirements. Each pin now records the refetched response hash as `definition_sha256` and the original as `original_definition_sha256`, so the two are never conflated. The freeze schema is `gamma.s20-official-execution.v2`.

`test_protocol.py` adds two source-free controls: a change confined to an unselected language is recorded rather than rejected, and changes to content, the API or a selected template are still rejected. All 21 controls pass. No candidate was executed in this repair.

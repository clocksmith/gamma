# Hack2Hire chunk02-a: 18 groups, 24 variants, inferred specifications

Worklist: 18 Hack2Hire coding groups (Find the Most Common Ads through MultiStream Reader), every variant. Identity is `hack2hire:<variant id>`; sources are `python/<variant id>.py` and `javascript/<variant id>.js`.

**Every specification here is inferred**, by the claude-opus-5-5 subagent on 2026-10-28, from the public group preview (`payload.data.contentPreview`), title and `algorithmTags`. No official statement, locked content or solution was read. `contracts.json` records, per variant, the preview `response_sha256`, the basis fields, an uncertainty note, `spec_basis: inferred`, the inferred spec in the author's own words and the chosen `inferred_interface`. Previews are paraphrased, not copied.

Function variants export `solve(...)` plus `Solution().<name>` (Python) and `module.exports.<name>` (JavaScript). Design variants (CreditSystem x2, IpFirewall, DistinctPIIValuesCounter x2, MultiStreamReader) export the native class plus a `solve(operations, arguments)` trace adapter; `native-bindings.json` and `native_harness.*` follow requested-22-a, adapted to string uids and constructor arguments. Concurrency and randomness are modelled as deterministic functions over injected inputs (Matrix Transpose with Workers simulates contiguous worker blocks; Generate Random NFT consumes an explicit `randoms` list; MultiStream Reader wraps injected strings in read-only Stream objects).

`oracles.py` holds independent brute-force or literal references and inferred-domain validators; `cases.py` generates small random, boundary and maximum cases; both were frozen before any candidate source existed (`pre-source-reference-freeze.json`). One later amendment lowered the inferred High Correlation Seller session bound from 50 to 20 because its maximum case exceeded the CPU budget under node --jitless; no candidate changed for it.

Author-local results (`checks.json`): 5234/5234 cases pass in each language; native harness 2632/2632 observations; heaviest case 0.49 s (python3) and 0.31 s (node --jitless) for two executions per case; peak RSS under 160 MB. These are runs against the author's own references, not qualification. Every semantics file has `qualification.status: unknown`.

`study-records/` holds `study.record.v1` records (contract, two implementation artifacts, a source-native study-content artifact required by the schema's `native` Ref, and an approach per variant), generated from `contracts.json`, `design.json` and `study-content.json` and validated by `test_study_records.py` against `projects/problem_catalogue/schema.v1.json`.

Largest inference risk: Group Loans by Top-Level Company. Its cached preview describes the DistinctPIIValuesCounter problem (the Live Fraud Detector text), not loans, so both variants are inferred from the title alone.

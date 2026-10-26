# Extrema binding alignment — v3 proof checkpoint, not qualification

**38/38 native parser controls and8/8 exact source syntax checks pass.** Independent source-specific review and hash-bound numeric input audits cover802 exact finite cases. No private candidate was executed or transformed in this lane. No new source is qualified.

The one proposed composable feature permits directly resolved, unshadowed Math.min/max calls only. It reuses the existing parser, capture graph, canonicalizer and exact AST occurrence-to-binding checker. Current implementation is `alignment-v3.mjs` with `controls-v3.mjs` / `probe-v3.mjs`. Preserve properties, globals, APIs, literals, operators and expression order; no intrinsic rewrites or constant folding. Every call argument requires a full nonmutating syntax tree including conditional tests, member receivers and indices. Dynamic primitive-Number typing and untouched runtime intrinsics are separate trusted audit obligations, not inferred from syntax.

| Original ID | Finite cases | Syntax/source review | Remaining admission |
|---|---:|---|---|
|123|117|Pass; exact historical baseline400 owner|Runtime/caller/full replay pending|
|55|66|Pass|Runtime/caller/full replay pending|
|1014|106|Pass|Runtime/caller/full replay pending|
|1121|103|Pass|Runtime/caller/full replay pending|
|1375|91|Pass|Runtime/caller/full replay pending|
|1725|83|Pass;747 nested rows each exactly2 Numbers|Runtime/caller/full replay pending|
|1732|110|Pass|Runtime/caller/full replay pending|
|2873|126|Pass|Runtime/caller/full replay pending|

123's current service implementation is a different newer source/specification. The initial mismatch failed closed before payload opens; the seven-source audit was retained. The exact original123 was subsequently bound through the unchanged existing JavaScript receipt adapter to its independently verified original baseline400 source/runtime/tests/effects chain. Its117 original arrays have lengths2..39. No current-service tests were substituted, and the declared eight-ID denominator was never silently reduced.

## Failures and corrections retained

- `alignment.mjs`: unrun first proof omitted conditional-test/member-receiver recursion. Independent review rejected hidden mutation counterexamples before admission.
- `alignment-v2.mjs`: recursive purity corrected; preserved as a linked intermediate. V3 additionally excludes optional-chain syntax from the explicitly direct-call-only feature.
- Original seven-source `prepare_audit.py` and linked eight-source `prepare_audit_v2.py` remain separate; metadata-only preparation failures are recorded in RESULT-v3.
- `REVIEW.md` is the historical first review request, not current status.
- Original bounded host verifier succeeded, but quadratic concatenation made the126MB runtime hash slow. Separate `verify_probe_v2.py` uses linear chunk collection; four public synthetic reader tests pass. No candidate run was repeated.

## Replay proposal, not authorization

First authenticate an independently trusted receipt binding exact source, cases, effects and runtime before supplying any proof booleans to the transform API. Separately attest the pinned fresh runtime, unchanged harness and untouched Math/standard Array iterator behavior. Parser results do **not** establish that runtime condition.

Only after those gates and independent review: generate private matched format-only and role variants, retain original arms and all875 fallbacks, freeze24 source-arms, and replay all802 original cases per arm: **2,406 checks /87 calls** using unchanged32-case batching and original typed result/error/mutation/alias oracle. Proposed child caps remain3CPU seconds/8wall seconds/1GiB/64MiB V8/4MiB output, with a bounded900-second owned-process supervisor. No replay freeze or launch exists yet.

Eight originals total1,053 bytes; this is a small composable feature increment, not hard-tail success. No tiny-only global refit. All300 owners/875 fallback variants and formatting controls remain required. M1 is UNMET.

## Publication boundary

Code, independently authored public parser strings, counts, source IDs and hashes only. No original/renamed/formatted source payloads, dictionaries, packets, cases or native raw logs are published. See RESULT-v3.json and PUBLICATION-ALLOWLIST-v1.json. Existing parser dependencies and cleanup owner are unchanged; their provenance was published in earlier sibling checkpoints.

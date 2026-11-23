# Fixed canonical source comparison v1 (proposed)

**Status:** run once as [fixed-source-v1](fixed-source-v1/FREEZE.md). Its frozen rules and [results](fixed-source-v1/RESULTS.md) are the record of that run.

Freeze the manifest, policy, metrics, baseline implementations and analysis plan
before execution. This is a protocol, not a run or an approved promotion gate.
It asks how compactly fixed source can be represented, not whether it transfers to
unseen source, how well a model solves new problems, or how quickly a person enters it.

## Hypotheses

1. Given the same maximum entry count, entry length and stored dictionary
   bytes, structured reusable literals lower aggregate emissions on this fixed
   canonical corpus relative to the strongest matched BPE/frequency baseline,
   while preserving exact reconstruction of all programs.
2. For matched JavaScript/Python tasks, one shared literal dictionary can beat
   two language-specific dictionaries on the same objective under an equal
   **total** entry/byte budget. Shared vocabulary is an empirical question, not a
   premise. Report each language as well as the pooled result.

## Inputs, arms and measurements

- Pin a manifest with one immutable canonical byte sequence per task and language,
  source hash and provenance. Build and measure every codebook on this same
  complete paired corpus. This is an in-sample optimization; do not open a holdout.
  No rewrites, macro expansion, injected wrappers, or raw escape. Every selection
  expands to exactly its stored bytes. Alternate source versions are a separate
  experiment.
- Freeze a grid of at-most entry slots `K`, max UTF-8 entry length `L`, and
  at-most dictionary bytes `B`, before evaluation. Charge the actual serialized
  dictionaries including framing. Measure literal payload emissions, emitted
  bits, complete packet bytes (framing and padding included) and total source
  bytes, separately. For separate dictionaries, charge both bodies and routing
  metadata and optimize allocation within the combined budget. Use the same
  output framing and declared selector-width policy across each contrast.
- Build strong document/occurrence-frequency dictionaries and BPE from the same
  fixed corpus. Compare BPE with its ordinary merge encode and, separately, exact
  shortest parsing of the **same** learned codebook. For the vocabulary-design
  comparison use the same exact parser for all codebooks. Document codebook
  construction and the shared tie-breaker; do not give the candidate a stronger
  parser or a hidden fallback unavailable to its baseline.
- Measure singleton-only `[1,1]`, mixed `[1,L]`, and strict non-singleton
  `[2,L]` independently where feasible. Enforce the corresponding length rule
  during both candidate generation and verification. Freeze any cross-document
  witness/whole-program restriction and apply it consistently; if ordinary BPE
  does not obey it, report the unconstrained BPE arm separately with a matched
  constraint-compliant control. Do not infer the non-singleton result from the
  older `greedyDP` arm.
- Independently decode every counted result and compare raw output bytes against
  its pinned hash. Compare aggregate emissions only between arms covering 100%
  of the frozen corpus. For incomplete arms report missing IDs and explicitly
  labeled matched-support diagnostics, not apparent wins from dropped cases.
  List bounds separately from verified optima; report per-program differences,
  not a generalization estimate.

## Changes and stop rules

Tune candidate search, dictionary generation and budget allocation within this
fixed policy and comparable work limits; record seeds, runs and exact output
identities. If results motivate changing the corpus, eligibility, accounting,
metric, constraints or acceptance bar, record a new version before running it.
Use the same corpus again for a labeled in-sample policy variant if appropriate.
Preserve original manifests, code revisions, receipts, and null findings. Do not
reuse an old result under the new policy or read a preserved holdout.

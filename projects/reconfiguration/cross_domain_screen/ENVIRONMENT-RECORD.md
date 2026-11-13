# Append-only environment history

Record environment observations separately from model outputs and frozen scores.
The shader study's original evaluator still computes its original ratios and
decision. Concurrent 27B execution makes overlapping performance observations
contended; stopping an idle resident service changes memory conditions but does
not demonstrate isolated GPU timing. Keep every quality output in its original
denominator.

Use a new JSONL ledger. Every line is an observed event with schema
`gamma.reconfiguration-environment-event/v1`. Never edit an earlier line. Append
corrections as new events identifying the earlier event. Before final reporting,
pin the complete ledger's byte SHA256 and retain every referenced receipt. The
following is a **template**, not evidence; replace every placeholder and change
status to `observed` only for an actual observation:

```json
{
  "schema": "gamma.reconfiguration-environment-event/v1",
  "status": "template-not-observed",
  "eventId": "UNIQUE_EVENT_ID",
  "previousLineSha256": null,
  "observedAt": "UTC_OBSERVATION_TIMESTAMP",
  "targetInputFileSha256": {
    "runtimeLock": "EXACT_WGSL_RUNTIME_LOCK_FILE_SHA256",
    "stageLock": "EXACT_WGSL_STAGE_LOCK_FILE_SHA256"
  },
  "host": "jupiter",
  "device": "EXACT_RECORDED_DEVICE",
  "kind": "provider_retired",
  "description": "FACTUAL_OBSERVATION_WITH_MEASURED_BOUNDARIES",
  "isolationQualification": "unknown",
  "sources": [{"path": "RELATIVE_RECEIPT_PATH", "sha256": "EXACT_FILE_SHA256"}]
}
```

Serialize each event as one JSON line ending in newline. The first
`previousLineSha256` is null; each next line records the SHA256 of the preceding
**exact line including newline**. Bind the target runtime/stage **file** hashes,
not their internal canonical object hashes. Referenced receipt hashes identify
the recorder's sources; the reporter does not open those sources or any oracle.

Kinds include `provider_retired`, `workload_started`, `workload_ended`, `overlap`,
`phase_summary`, and `correction`. Observed events must have nondecreasing
`observedAt` timestamps. `overlap` events carry
`interval: {startedAt: ISO_TIMESTAMP, endedAt: ISO_TIMESTAMP_OR_NULL}` and
`isolationQualification: "contended"`. Use actual model-load, preparation,
generation, reset and cleanup event timestamps from both workloads. An open
interval remains ongoing; never invent its ending. A correction preserves the
original observation; this conservative reporter will not upgrade contended
evidence to isolated evidence.

After completion, optionally append `phase_summary` events using the same
interval object and a `timingSummary` object:

```json
{
  "requestCount": 0,
  "requestIdsSha256": "SHA256_OF_SORTED_REQUEST_ID_JSON_ARRAY",
  "physicalRequestMs": 0,
  "attributedEndToEndMs": 0
}
```

These numbers must be measured from the referenced completed journal. They are
not defaults to publish. Record distinct phases for the resident-provider period,
retirement transition, post-retirement before parallel work, overlapping 27B
load/inference, and after overlap if each actually occurs. A request spanning a
boundary belongs in a separate spanning/transition phase; do not fractionally
allocate its cost without instrumentation. Within each summary, count each
physical request once. Shared submissions and best-of-k totals are not extra
physical requests. Phase comparisons are descriptive and can differ in task,
condition and cache-arm composition; no causal speedup follows from them.

Final report command adds the optional argument:

```bash
python3 -m projects.distillation.wgsl.channel_gain.report_confirmation \
  --protocol PROTOCOL.json --evidence AUTHENTICATED_EVIDENCE.json \
  --environment ENVIRONMENT.jsonl \
  --json-output NEW_REPORT.json --markdown-output NEW_REPORT.md
```

Without a ledger the report labels isolation unknown. With any observed overlap
it labels isolation contended. No ledger changes raw costs, task outcomes,
frozen thresholds, quality denominators or the original joint decision.

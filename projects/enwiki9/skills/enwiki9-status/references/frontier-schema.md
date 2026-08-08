# Frontier Schema

`docs/hutter_frontier.json` is the curated research frontier. It complements
the generated operational `docs/status_receipt.json`; it does not replace it.

## Candidate Fields

- `id`, `name`, `rank`, `status`, `evidence_tier`: required identity fields.
- `scope_bytes`: measured raw input scope.
- `archive_bytes`, `program_bytes`, `forecast_score`: counted metrics when known.
- `measured_gain_bytes`, `gain_bytes_per_1m`: direct matched measurements.
- `score_credit_bytes`: bytes allowed to affect the constructive forecast;
  always zero for idea, proxy, oracle, and causal shadow rows.
- `source_paths`: repository-relative or absolute receipt paths.
- `source_required`: whether missing source paths fail strict validation. When
  false, assertions against absent historical overlays are marked skipped;
  assertions against sources that are present remain mandatory and fail closed.
- `metric_assertions`: optional JSON-pointer checks binding a candidate field
  directly to a machine-readable source receipt.
- `decision`, `next_gate`, `disqualifiers`: concise current interpretation.
- `parent_candidate_id`: optional direct lineage parent.
- `additional_runs`: optional source-bound measurements for other scopes or
  corpus populations of the same candidate. Each run requires `run_id`,
  `scope_bytes`, `population`, `source_paths`, and JSON-pointer
  `metric_assertions` for decisive duplicated metrics.

## Status Values

Use `active`, `promotable`, `retired_unchanged`, `quarantined`, or
`historical_control`. A broader idea can remain active while one implementation
is retired; give them separate rows.

## Arithmetic

```text
target_score = 105000000
margin_bytes = target_score - forecast_score
debt_bytes = max(forecast_score - target_score, 0)
required_gain_B_per_M = debt_bytes / 1000 + added_program_bytes / 1000
```

Do not infer a full score from a measured gain unless the candidate records a
specific projection basis and fully counted program size.

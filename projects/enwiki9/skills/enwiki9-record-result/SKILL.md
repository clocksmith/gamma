---
name: enwiki9-record-result
description: Record one completed enwiki9 result in the canonical frontier when an immutable receipt and explicit promotion, retirement, or quarantine decision are supplied.
---

# enwiki9 Result Recording

## Prerequisites

- Run from the Gamma repository root and read the enwiki9 AGENTS/CATSCAN chain.
- Supply the immutable result receipt, candidate identity, corpus scope, archive/program
  bytes, roundtrip result, evidence tier, source paths, and explicit disposition.
- Read `projects/enwiki9/docs/hutter_frontier_schema.md`.

## Procedure

1. Verify every supplied source path and bind duplicated numeric fields with metric
   assertions where supported.
2. Add or update the candidate row in `docs/hutter_frontier.json`; preserve retired and
   quarantined history.
3. Give proxy, oracle, causal-shadow, and idea evidence zero score credit.
4. Grant full-corpus official status only for exact 1,000,000,000-byte scope, complete
   program accounting, successful roundtrip, and score at or below 105,000,000 bytes.
5. Normalize and check generated views:

   ```bash
   python3 projects/enwiki9/tools/enwiki9_normalize_receipts.py
   python3 projects/enwiki9/skills/enwiki9-status/scripts/report.py \
     --project-root projects/enwiki9 --strict
   ```

## Validation

The normalizer and strict reporter pass, all source paths resolve, arithmetic and metric
assertions agree with the receipt, and a second normalization produces no diff.

## Stop Conditions

Stop without an immutable receipt or explicit disposition. Stop on missing sources,
scope ambiguity, failed roundtrip, incomplete program accounting, or conflicting
candidate identity. Do not invent a research conclusion or next gate.

## Outputs

Updated source-bound frontier and generated receipt/status views with the validated
candidate disposition.

## Side Effects

Mutates canonical frontier and generated evidence views. It does not launch experiments,
alter running jobs, delete historical candidates, commit, push, or submit a prize entry.

# SAME-R Machine-Readable Contracts

This directory turns the SAME-R documentation into validation targets.

## Files

- `same-r-contract-suite.schema.json`: JSON Schema for a complete validation
  bundle. Each reusable object is defined under `$defs`.
- `example.same-r-contract-suite.json`: canonical synthetic example. It is not
  an experiment result or capability claim.
- `validate_same_r_contract.py`: dependency-free validator for the semantic
  invariants that JSON Schema cannot express by itself.

The normative prose is in:

- [`../README.md`](../README.md);
- [`../CAUSAL_AND_EVIDENCE_CONTRACTS.md`](../CAUSAL_AND_EVIDENCE_CONTRACTS.md);
  and
- [`../SELECTOR_AND_SATURATION.md`](../SELECTOR_AND_SATURATION.md).

## Validation

```bash
python projects/samer/contracts/validate_same_r_contract.py
python tests/test_samer_contracts.py
```

The validator checks:

- schema and example are valid JSON;
- exact contract field sets;
- identifier, revision, and SHA-256 shapes;
- disjoint accepted/rejected/blocked/invalidated/saturated histories;
- participant-role and scoped-label-authority references;
- exact model, base-checkpoint, tokenizer, adapter-initialization, initial
  parameter, and trainable-parameter lineage;
- ordered row IDs, order hashes, counts, consumption, and resume state;
- retry attempt retention and budget disposition;
- checkpoint and item denominator reconciliation;
- contamination checks, access audit, and overall disposition;
- measurement/adjudication typing;
- selection candidate/rejection completeness;
- recursive parent/child budget accounting; and
- formal saturation reason, pending-work, and budget consistency.

## Artifact Granularity

The checked-in example is a bundle so cross-object references can be tested in
one command. A production system SHOULD store each object separately and bind
it by repository revision, path, and SHA-256. A production bundle may assemble
those immutable pointers for replay.

The schema `$defs` are the canonical object names:

- `approachRegistry`;
- `participantRegistry`;
- `labelAuthority`;
- `causalContract`;
- `runContract`;
- `contaminationAudit`;
- `metricEvidence`;
- `trialReceipt`;
- `selectionReceipt`; and
- `saturationDecision`.

## Hash Rule

For an object containing its own `sha256` field, hash canonical UTF-8 JSON with
that self-hash field omitted. Array order is meaningful unless the object
explicitly declares a canonical sort rule.

## Evolution

Schema changes increment `schemaVersion`. A validator MUST continue to reject
unknown fields for a known version. Adding a field without a versioned schema
would allow two executors to assign different meanings to the same contract.

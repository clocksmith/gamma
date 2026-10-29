# Study records for authored cohorts

Every authored cohort also writes its content as `study.record.v1` records, the schema owned by [problem_catalogue](../../../../problem_catalogue/README.md). The generated schema is [schema.v1.json](../../../../problem_catalogue/schema.v1.json). Do not edit it; if a field is missing, report it to the problem_catalogue owner.

The existing cohort files (python/, javascript/, semantics/, contracts.json, oracles.py, cases.py) stay as they are. The records are written alongside them in `study-records/`, one JSON file per record, named `<kind>--<id with ':' replaced by '_'>.json`.

## Records per variant

Problem records are not authored here: migration builds them from the question bank. Refer to the problem by `problemId` (`hack2hire:<post id>` or `leetcode:<number>`).

| Kind | id | Content |
|---|---|---|
| `contract` | `contract:<problemId>:<variant id>:authored-v1` | `variantId`, `contentScope: "authored"` (or `"full-statement"` only for an official statement you did not copy), `statement` = the spec in your own words, plus `requirements`, `constraints`, `assumptions` (every inference, with its basis), `clarifyingQuestions`, `examples` (your own), `interfaces` (one per language, `kind` function or class, `declaration` = the signature), `effects`, `comparison` |
| `approach` | `approach:<problemId>:<variant id>:v1` | `contract` Ref, `title`, `representation: "coding"`, `explanation`, `chooseWhen`, `tradeoffs`, `invariants`, `hints` (ordered, least to most revealing), `stages` (at least: reasoning, coding, validation; each with `question`, `explanation`, `rationale`, `instructions`, `hints`, and `artifacts` Refs on the coding stage), `sequenceStatus: "draft"` |
| `artifact` | `artifact:<problemId>:<variant id>:<language>:v1` | `type: "implementation"`, `language`, `file` = FileRef to the source file (path relative to the gamma root, sha256, bytes, mediaType `text/x-python` or `text/javascript`), `executionKind: "code"`, `complexityClaims`, `contract` Ref, `approachId` |

## Rules

- Every record has `schema: "study.record.v1"`, `version: 1` and `origin` (SourcePointers with `repository: "gamma"`, `revision: null`, the cohort file path and its sha256).
- Each `present` field carries `provenance` pointing to the cohort file it came from. Use `unknown`, `missing` or `not-applicable` with a reason instead of inventing content. A present empty list means "checked, none".
- A `Ref` carries `kind`, `id`, `version`, the record's path and the record file's sha256. Write records in dependency order (contract, then artifacts, then approach) so the hashes are final. References must stay acyclic.
- No qualification, admission or evidence records. Local runs stay in `checks.json`.
- Validate every record with `jsonschema` against `schema.v1.json` in a `test_study_records.py`, and include the records in the cohort's manifest and SHA256SUMS.

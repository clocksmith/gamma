# Hard10 JavaScript/Python candidates (2026-10-25)

Status: authored, locally tested candidates; not Gamma-qualified or admitted.

This additive import retains the 20 source files unchanged from the conversation
archive. IDs: 10, 42, 84, 85, 123, 546, 564, 992, 1074 and 1187. Both languages
expose synchronous `solve(...)` with the same ordered positional arguments and
a native LeetCode alias. Each implementation has its original semantics record.

## Evidence boundary

`assignment.json`, `contracts/` and `provenance/selection.json` preserve the
original source-selection and public-problem summaries at Gamma commit
`7290ac480db36698b4c69e677f4f51172dd738bd`. These are candidate contracts, not
substitutes for Gamma's frozen per-problem behavior/effect contracts. No catalogue
status, runtime policy, protected population, original source, or oracle changed.

`VALIDATION.md` and `validation/attempt-001/report.json` are retained external
local evidence: 20 syntax checks and 50,283 paired cases passed in the original
ordinary-process environment. They are not a new Gamma sandbox run or an external
receipt-verifier attestation. Their no-repository-write fields describe that
original run, before this separately authorized source import.

Full generated cases and worker outputs remain in the supplied conversation ZIP,
not this Git tree. The original inventory is retained at
`provenance/archive-SHA256SUMS`. The original README is `ORIGINAL_README.md`.
This tree contains the same generators/runners and original summary reports.

Original archive SHA-256: `808a4a418a77957c12d4b71a224eb3da7d7c78c4740196e6313b67bbf487633c`.

## Reproduce the local checks

From this directory, with Node.js and Python already available:

```sh
python3 validation/build_cases.py
python3 validation/validate.py
```

These commands generate cases and a new numbered attempt; they do not run the
Gamma judge, promote sources, train a model, download dependencies, or deploy.
Keep any failures. A coordinator must compare the frozen Gamma interfaces,
mutation/alias effects and runtime/test bindings before separately qualifying
either language. Existing qualified candidates are not replaced by this import.

## Component handoff

Component: algorithm solver candidate findings. Intent: preserved.
Boundary effects: additive source/evidence package only; no serving or admission.
Commit checks: original payload SHA-256 verification; 20 source syntax parses;
UTF-8/JSON parsing; source Git-blob identities verified against the archive.
No behavioral rerun or qualification is claimed for the import itself.

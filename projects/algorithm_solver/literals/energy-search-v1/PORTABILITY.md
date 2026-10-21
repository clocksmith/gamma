# Portable adapter boundary

The proposed checkout destination is `projects/algorithm_solver/literals/energy-search-v1/`. This is staging for a reviewed **local commit only**, not publication approval. Canonical repository files are not edited by this lane.

The original private run, source modules and frozen results remain byte-for-byte unchanged. The portable copy makes only these implementation changes:

1. `harness.py` resolves sibling `../joint-v1/reachable_core.py` and `../readable-v1/literal_codec.py`, retaining their exact existing hashes. There is no task-path, environment-variable or arbitrary dependency fallback.
2. `fixtures.py` replaces private source-path reads with the pinned `human-seed-fixture.json`: nine general snippets, their hashes, witness IDs/full-source hashes, original receipt identity and explicit receipt-needed flags. No full private program or original test body is included. Synthetic program text and split construction are unchanged.
3. The corresponding provenance test checks immutable fixture/snippet/witness-hash integrity instead of reopening private source files. This is a deliberately narrower provenance check, not new semantic qualification.
4. `run_checks.py` records dependency paths relative to the literals directory rather than absolute task paths. Its budgets, test suite, candidate policies, exact accounting and search procedures are unchanged.
5. Documentation links and commands use checkout-relative paths. Raw synthetic run artifacts are locally reproducible; the reviewed staging allowlist includes aggregate receipts only.

Pinned dependencies:

- `joint-v1/reachable_core.py`: SHA256 `74b69275995f068ab227cdbc895984c2aa14ed98a971ff3d86bda14264ca7899`.
- `readable-v1/literal_codec.py`: SHA256 `64585df01200488e834540986f8ef99703dd99cecc76808a2b9654e1ea318afe`.
- `human-seed-fixture.json`: SHA256 `7c733e95ea3fd4464156076d02c343015eb0ef555c5caaba1a506e30f24d9b2d`.

The root coordinator owns shared-core integration. This package does not duplicate that core or the codec inside the energy-search directory. Tests import those pinned siblings, so a checkout missing them fails visibly.

All qualification claims remain unchanged: zero real problems qualified here, zero candidate-source execution, zero training and no trained-model quality result. Readable lines may be partial blocks. Synthetic split labels do not imply unseen evaluation. Real-data use still requires coordinator-approved source/contract/receipt envelopes and protected-boundary clearance.

## Independent-review repairs

The final portable revision additionally closes same-contract, direct-scoring and canonical-ID/alias eligibility gaps, restricts alternatives to the same language, and completes qualification schema requirements. Thirty mechanism tests and the unchanged 18 synthetic arms pass; no trained scorer is added. The runner now measures its stated new-file budget per invocation while retaining historical output. Original private artifacts and the initial portable receipt remain unchanged. See [review repair evidence](receipts/review-repairs-v2.json).

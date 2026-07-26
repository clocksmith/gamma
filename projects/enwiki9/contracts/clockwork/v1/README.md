# Clockwork Contracts v1

This directory is the canonical public contract authority for the Clockwork
research bridge. Reploid and m3t4 may generate digest-bound types and validators
from these files, but those projections do not become schema authorities.

Validate the contract set:

```bash
python3 projects/enwiki9/tools/clockwork_contracts.py
```

Validate an artifact:

```bash
python3 projects/enwiki9/tools/clockwork_contracts.py path/to/artifact.json
```

`contract-set.json` binds the six exchanged artifact schemas. Its
`contractSetDigest` is the SHA-256 of the canonical JSON object after removing
that digest field. Individual schema digests use the same canonical JSON
profile: UTF-8, sorted object keys, no insignificant whitespace, and no
non-finite numbers.

Artifact validation also verifies the current contract-set identity and each
schema's self-digest field. Candidate identity is the SHA-256 of the decoded
canonical genome bytes; mutable lineage or transport metadata is not part of
that candidate digest.

The schema files are public. Private application certificates, theorem
holdouts, and verifier material are not stored here; public route bindings
carry only their digests.

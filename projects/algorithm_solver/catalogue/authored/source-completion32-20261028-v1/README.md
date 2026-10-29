# Original paired source completion: first 32 problems

Paused at the owner’s request for organization/schema review. This directory is an
uncommitted authoring batch, not a canonical problem registry or an active release.
It adds 32 original JavaScript/Python source pairs without replacing older sources.

## Contents

- `manifest.json`: stable LeetCode ID, title, official URL/slug, pinned definition
  response hash, method name, ordered typed parameters/return, per-language source
  path/hash and development evidence. Each problem has two source records.
- `python/<id>.py`: module-level `solve`, official method alias, and `Solution`
  wrapper. `javascript/<id>.js`: CommonJS `solve` and official method export.
- `development_checks.py`: independent small-case reference algorithms and the
  observation adapter. Tree arguments are native objects with `val/left/right`;
  the adapter’s JSON normalization is observation transport, not the native API.
- `development-results.json`: exact-source exposed-development results.

## Contract and evidence boundaries

All 32 public definitions were fetched on Jupiter only after exact-ID statement
access checks through the existing six-anchor gate. Full responses remain private
under `~/.local/share/gamma-source-completion-20261028`; this batch contains hashes
and API metadata, not redistributed statements or copied third-party solutions.
Inputs are those pinned specifications and newly generated development arguments.
There are no new model dependencies or downloaded weights.

All 64 sources passed syntax checks. Development execution used the existing Linux
bubblewrap sandbox with no network, 3 CPU seconds, 8 wall seconds, 1 GiB address
space and 16 MiB output. Expected values remained outside isolation. The retained
result records 1,142 completed calls across 64 programs, all passing. These are
small exposed-development checks by the author, not independent qualification,
full-domain/resource qualification, official judge acceptance or catalogue adoption.
Native tree mutations are checked separately for 450 and 538; other inputs must
remain unchanged in this batch’s development observations. Optional no-extra-space
follow-ups (such as 501) are not claimed by the explicit-stack implementations.
363 uses sorted-prefix insertion: O(min(rows,cols)^2 * max(rows,cols)^2) worst-case
time, with the shorter dimension paired; no logarithmic insertion claim is made.

## Reproduce the development check

From the Gamma root on the provisioned Linux host:

```sh
python3 projects/algorithm_solver/catalogue/authored/source-completion32-20261028-v1/development_checks.py \
  --repo-root "$PWD" --output /PRIVATE/NEW-OUTPUT \
  --gate /PRIVATE/EXISTING-SIX-ANCHOR-DESCRIPTOR --gate-sha256 EXACT-DESCRIPTOR-HASH
```

Only explicitly supplied gate metadata and this batch’s source files are opened.
The entrypoint revalidates source hashes and access before every candidate read.
Raw streams live under the private output path; no global catalogue, recognition
index, source admission, serving locator or qualification status is changed.

## Next review

Agree one canonical separation of problems, implementation variants, native APIs,
adapters, provenance, checks and admission records before expanding the next batch.
Do not treat filenames, existing catalogue labels and official frontend IDs as
interchangeable without an identity binding. The metadata-only worklist remains
in ignored `runs/source-completion-20261028`; it is a location census, not proof
that unlocated implementations were never written.

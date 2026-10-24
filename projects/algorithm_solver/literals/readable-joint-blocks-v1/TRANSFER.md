# Private development-input transfer

The dot checkout has runnable code and the public three-problem readable pilot,
but not the private inputs needed for the existing **300 fit / 100 consumed
development-validation** comparison. A pilot cannot qualify M1's frozen
400/500 target. This transfer supplies development inputs only; it neither
qualifies new sources nor opens an evaluation gate.

## Pinned dependency

At source commit `2fb7c7391832d2a2dfdef7f1b1f0752359926596`, the
[source contract](https://github.com/clocksmith/gamma/blob/2fb7c7391832d2a2dfdef7f1b1f0752359926596/projects/algorithm_solver/literals/cost-decomposition-v1/contract.json) names the exact 400
permitted source paths/hashes and both dictionaries. The
[qualification contract](https://github.com/clocksmith/gamma/blob/2fb7c7391832d2a2dfdef7f1b1f0752359926596/projects/algorithm_solver/literals/name-search-v1/contract.json) pins their 800 case and
baseline files and the original population-metadata hash. The metadata-only
allowlist is derived in memory by [transfer.py](transfer.py) from those two
existing local contracts. Their exact SHA256 commitments are pinned in the
tool. A missing or changed contract fails closed, regardless of the current
branch; the tool does not fetch replacement files or consult private inputs
to construct its policy. No duplicate metadata manifest is published.

Supply the existing private work root as `WORK_ROOT` through the private
conversation. Do not add workstation paths, account names or credentials to
this document or the transfer tool.

Required payloads are:

- 400 shared-style sources under `style150/submitted/` or `scale500/submitted/`.
- 400 corresponding `population500/<id>-tests.json` files.
- 400 corresponding `population500-baseline/qualification/baselines/<id>.json` files.
- Two `roles/run-v1/dictionaries/L-R-{128,256}.json` dictionaries.
- Only permitted metadata rows from the hash-pinned `population500/manifest.json`.

The repository contracts contain commitments, not the required private bytes.
Obtain the exact permitted development package from its existing custodian;
do not substitute a different corpus or treat hashes as reproducible inputs.

## Export where the existing private inputs reside

These commands are for the owner to run from the updated Gamma repository root
on the machine containing the private work directory. This document does not
authorize dot to operate that machine.

```sh
python3 -B projects/algorithm_solver/literals/readable-joint-blocks-v1/transfer.py export \
  --work WORK_ROOT \
  --archive PRIVATE_ARCHIVE_PATH
```

The archive destination must not already exist. The exporter opens only the
allowlisted payload files and the single pinned metadata file, verifies their
hashes, and writes a private archive. It emits 400 filtered metadata rows, not
the full 500-row manifest. It does not recursively scan or execute sources.

Upload the archive privately to the existing dot conversation or Library.
Never commit the archive, sources, cases, baseline observations, dictionaries
or imported directory to public Git. Communicate the SHA256 printed by the
export command independently in the private conversation. Do not derive the
trusted hash from an unverified downloaded archive or its internal receipt.

## Import on dot

After the private upload is materialized locally, replace `PRIVATE_ARCHIVE_PATH`,
`NEW_PRIVATE_DESTINATION` and `VERIFIED_EXPORT_SHA256` with the privately supplied
local paths and independently received export hash. Run from the repository root:

```sh
python3 -B projects/algorithm_solver/literals/readable-joint-blocks-v1/transfer.py import \
  --archive PRIVATE_ARCHIVE_PATH \
  --archive-sha256 VERIFIED_EXPORT_SHA256 \
  --destination NEW_PRIVATE_DESTINATION
```

The destination must not exist. The importer checks the archive hash, exact
member allowlist and every pinned payload hash before writing. It rejects
extras, duplicate members, symlinks, path traversal and nonzero trailing data.
Filtered metadata is saved as `population400/manifest.json`. Do not rename it
to the original manifest or claim its bytes match the original full-manifest
hash. A SHA256 commitment to the complete original cannot authenticate a
filtered subset by itself; the trusted export hash binds that derivation.

The final held-out 100 and protected 66 remain excluded. Do not run historical
all-500 pool loaders: some read all sources before selecting the development
partition. New consumers must apply this explicit allowlist before opening
files. Import success establishes transfer integrity, not correctness,
independent confirmation, M1, M2 or M3. Candidate qualification still requires
the repository's functioning isolated judge; do not bypass it.

Focused synthetic verification, requiring Python's standard library only:

```sh
python3 -B -m unittest discover \
  -s projects/algorithm_solver/literals/readable-joint-blocks-v1 \
  -p test_transfer.py -v
```

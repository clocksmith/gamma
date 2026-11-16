# Selected retained artifacts

`retained_artifacts.py` uses Python 3.10+ standard library and Git. Publication
uses POSIX directory descriptors and atomic hard links. No Node, model libraries,
credentials, uploads or provisioning are required.

The initial backend is **already-public Gamma Git history**. A catalog binds each
original path to a full source commit, Git blob, SHA-256, size, executable mode and
canonical `raw.githubusercontent.com/clocksmith/gamma/<commit>/<path>` URL.
This reduces the current source tree; it does not shrink history/full clones or
provide WORM storage or a provider-enforced retention lock. Preserve published
history. Do not use this public backend for unpublished private material.

From the repository root, build only the explicitly selected committed files:

```sh
python3 tools/retained_artifacts.py build --revision FULL_COMMIT_SHA \
  --paths '["results/example/P.raw","results/example/P.rbz"]' --out CATALOG.json
```

Build requires the revision in local `origin/main`, streams only those Git
objects and disables promisor fetching. That local reference is **not remote
availability proof**. Before removing any tracked outputs, verify the catalog
against the published remote from an independent fresh checkout and perform the
required CPU verification. Canonical fixture inputs and JSON receipts remain
tracked under the migration's own classification.

```sh
python3 tools/retained_artifacts.py restore --catalog CATALOG.json --root RESTORE_DIR
python3 tools/retained_artifacts.py restore --catalog CATALOG.json --root RESTORE_DIR --fetch
python3 tools/retained_artifacts.py check --catalog CATALOG.json --root RESTORE_DIR
python3 tools/retained_artifacts.py check-boundary --catalog CATALOG.json --root REPO_DIR
```

Restore first tries local Git objects (`--repo LOCAL_REPO` overrides the current
directory). Only explicit `--fetch` permits missing blobs to be read from their
pinned public URLs. It rejects redirects, excess/truncated bytes, hash or identity
mismatches, path traversal, Git-internal paths and symlink destinations. Verified
bytes and modes are published atomically; divergent files and racing writers
are never overwritten. `--prefix PATH` selects a file or directory subtree.
Restoration does not execute, promote or qualify an artifact.

`check` requires all selected restored bytes/modes to match. `check-boundary`
checks the Git index and fails even when a cataloged output was force-added.
None of these commands removes outputs or modifies remote state.

Focused tests: `python3 -m unittest discover -s tests -p test_retained_artifacts.py`.

# enwiki9 archive-maintenance pilot

The project remains archived. This work inventories and restores retained
evidence; it does not authorize research, training, downloads or a new score.

[The classification candidate](classification-candidate.json) enumerates the
exact source revision, census, rationale and first nine output paths. The
classifier reads Git tree sizes/IDs and 1,239 original metadata declarations,
not sparse-worktree presence or live research directories. It disables Git lazy
fetches. Unresolved families remain protected, including mixed source/model
snapshots beneath `results/` and `results_preserve/`. An output later bound as an
input is protected too. Classification never authorizes editing a frozen source.

From the Gamma repository root, generate a small summary; full per-path JSONL
is opt-in and should stay local:

```bash
python3 projects/enwiki9/tools/archive_inventory.py --summary /tmp/enwiki9-summary.json
# Add --inventory /tmp/enwiki9-inventory.jsonl for the exact per-path candidate.
```

The first candidate comprises `{P,K,D}.{raw,rbz,repeat.rbz}` from
`results/raw_reverse_bz2250k_q0_v1/`: 1,188,018 logical bytes, three unique byte
identities totaling 396,286 bytes. The original experiment explicitly lists
these outputs and its artifact receipt binds their sizes/hashes. All JSON
receipts, the original codec, frozen experiment/source bindings and the bound
`operations/evidence/fixtures/dualstream_opening250k_v1.raw` input stay unchanged.

The nine binaries are now retained outside the maintained Git tree. Restore
them into an ignored directory or their original paths (existing files are
verified and never overwritten):

```bash
python3 tools/retained_artifacts.py restore \
  --catalog projects/enwiki9/docs/archive-maintenance/retained-artifacts.json \
  --root . --fetch
python3 tools/retained_artifacts.py check-boundary \
  --catalog projects/enwiki9/docs/archive-maintenance/retained-artifacts.json \
  --root .
```

`--fetch` explicitly allows downloads from the catalog's pinned public GitHub
URLs when local Git objects are unavailable. The catalog binds every original
path to its full source commit, Git blob, SHA-256, size and mode. The boundary
check examines the Git index and rejects even force-added retained binaries;
default CI runs it along with the focused archival tests.

[The restoration check](restoration-check.json) records a successful depth-one,
blobless GitHub clone with only the selected source files materialized, no
shared object store and no original historical commit locally available. It
restored all nine binaries using this command before their tracked copies were
removed. All six archives passed the original CPU decoder and exact encoder.

Verify the restored original repository-relative paths:

```bash
python3 projects/enwiki9/tools/verify_raw_reverse_restore.py \
  --restored-root RESTORED_REPOSITORY_ROOT
python3 -m unittest discover -s projects/enwiki9/tests -p test_raw_reverse_restore.py -v
python3 -m unittest discover -s projects/enwiki9/tests -p test_archive_inventory.py -v
python3 -m pytest -q projects/enwiki9/tests/test_raw_reverse_bz2_v1.py \
  -k 'not fixed_synthetic_cli_exact_raw_repeats_and_kernel_resources'
```

The verifier needs only the currently tracked exact original receipt, experiment,
fixture and codec bytes, each checked against a pinned SHA-256 before use. It
does not invoke Git or a network client, so a fresh shallow clone needs no old
commit or unrelated historical output. The original commit identifier in its
report is provenance, not an execution dependency. The focused test constructs
a plain-file source directory without `.git` and proves verification there.

Verification checks all nine restored identities, six original decoder inverses,
six exact original re-encodings, P/K equality and each arm's repeat identity.
Corrupt restored data or changed original source fails closed. The historical
codec itself is reused, not rewritten. To invoke it directly, use:

```bash
python3 projects/enwiki9/tools/raw_reverse_bz2_v1.py decode \
  RESTORED_REPOSITORY_ROOT/projects/enwiki9/results/raw_reverse_bz2250k_q0_v1/P.rbz \
  NEW_TEMP_OUTPUT_FILE
```

The existing codec tests passed eight portable cases on macOS. Their additional
`fixed_synthetic_cli_exact_raw_repeats_and_kernel_resources` test requires
Linux's `os.sched_getaffinity`; it was attempted and failed on that missing API,
then excluded without modifying the frozen test. CPU byte restoration establishes
neither historical timing/resource isolation nor full-corpus performance. The
migration does not change the archived project's scientific status.
A pinned GitHub-history URL is not WORM storage
and moving current-tree outputs does not shrink existing Git history.

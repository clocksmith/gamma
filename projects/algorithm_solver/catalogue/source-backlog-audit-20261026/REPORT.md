# Gamma source backlog: what to integrate, repair, and locate

## Scope and result

Source inspection base: `8c0fb7a0971396fcb15b5cd19ddb4b8912f1d946`.
Final remote-head check: `f9644b354173bd75060673f38a55a63460b1caf3`.
The complete `projects/algorithm_solver/catalogue/authored` Git tree is unchanged
between those observations: `df956b4b14289284fc802be68ff97a77349709fa`.
The later commit consolidates milestone records; this report does not replace
`catalogue/roadmap-v1.json` or change any repository ledger.

**The immediate backlog is not 1,209 unwritten problems. I located 128 already-written
problem pairs whose batch directories are absent from main, one specifically
reported unresolved JavaScript resource failure, and several contract-reconciliation
issues. The global number of genuinely unwritten implementations still requires
joining the private source catalogue.**

No solution was executed, imported, syntax-checked, or tested in this audit. No
repository file, catalogue status, commit, or remote branch was changed. Local
Python scripts processed metadata, existing patch text, and Git object hashes only.
The supplied local reconciliation helper has not been executed on the user's machine.

## 1. The reconciled source census

The full target ID list was reconstructed as the JSON array of strings `1` through
`4081`, formatted with two-space indentation and a terminal LF. Its 39,706 bytes
match the published SHA-256 exactly:

`bac70750171f4cdf62c928d4d8273bca0fb6355d00d73a81e9a849d2859ba632`

This establishes the ID denominator; it does not establish a source or problem
contract for every ID.

| Source collection | Distinct problem IDs | Meaning |
|---|---:|---|
| Recent published authoring batches | 1,526 | 3,052 Python/JavaScript source files, with exact directory-tree reconstruction. |
| Two supplied batches absent from published authoring directories | 128 | 256 source files already written, not new authoring work. |
| Additional legacy development IDs after deduplication | 264 | From the documented 300 paired candidates plus 100 Python candidates and linked JavaScript references. |
| **Both-language source evidence located in this census** | **1,918** | Existence/reference evidence, not a correctness or qualification count. |
| **Not located in these audited collections** | **2,163** | Reconcile with private sources and other source collections before assigning new implementations. |

The 23 published patch-batch trees all reconstruct to their main Git tree hashes.
Twenty match the original patch bytes directly. Three match after substituting
the nine currently published corrected source blob identities. This detects file
membership and byte-identity differences without executing a solution.

For language-specific location precision: this scope documents 1,723 public
standalone JavaScript IDs and 1,790 public standalone Python IDs. A further 67
JavaScript references belonging to the legacy development set are documented by
pinned reference records but their private source bytes were not read. The two
outstanding patches add 128 IDs in each language, with no overlap with these
legacy 400 IDs or the recent published batches.

The historical imported corpus is another important source collection. Its
`algsolve/corpus.py` explicitly builds over problems with a statement and a Python
solution, while its full-library audit has a separate metadata inventory. That
private/imported source coverage was not fully joined here. Therefore **2,163 is
not a count of globally missing Python or JavaScript solutions**. The count of
truly missing implementations is left null rather than inferred from permission,
qualification, patch totals, or missing public files.

## 2. Integration backlog: 128 pairs already exist

| Batch | Problems | Files | Supplied patch |
|---|---:|---:|---|
| `leetcode-medium-64-v2` | 64 Medium | 128 | `gamma-64-more-medium-solutions-v2.patch` |
| `leetcode-hard64-v2` | 64 Hard | 128 | `gamma-hard64-v2.patch` |

The full ID/title list is `already-written-patch-only.md`, with machine-readable
per-language source paths and hashes in `already-written-patch-only.json`.
Original supplied patches are included in `pending-patches/` in the audit ZIP.
They have not been applied or tested by this audit.

Examples from the Medium batch are #1311, #1493, #1594, #1654, #1674, #1786,
#2049, #2467, #2812, and #3202. Examples from the Hard batch are #295, #297,
#460, #895, #1032, #1172, #1483, #1622, #1825, and #2642.

Absence is established for their intended public batch directories. This is not
an assertion that every corresponding algorithm is absent from every private
store. Review existing local changes and applicable source/contract boundaries
before integration; do not regenerate these 256 files merely because the batch
names are missing from main.

## 3. Repair and reconciliation queue

### JavaScript #1743 — Restore the Array From Adjacent Pairs

**State: retained resource failure, not missing source.**

The original `catalogue/authored/leetcode-medium-32-v1/javascript/1743.js`
exhausted the pinned 64 MiB Node heap in a 32-case batch. The retained alternative
`catalogue/authored/packed-path1743-v1/javascript/1743.js` also has the failed
batch recorded. The checkpoint explicitly says no successful repaired-source
adoption occurred.

Next: attribute peak memory to candidate allocations, retained inputs/outputs,
and observer/batch behavior, then fix the responsible path under the unchanged
resource contract. A heap failure is not evidence that the mathematical graph
algorithm gives wrong answers. There is no fresh physical replay in this audit.

Authority: `catalogue/public-domain-qualification-hard32-wave2-numeric-v2/CHECKPOINT-DEPENDENCIES.md`
and `catalogue/public-domain-qualification-medium32-wave2-memory-v1/QUALIFICATION-RESULT-v1.json`.

### Legacy #1064, #1086, #1087, #1153, #2898 — reconcile domains

`literals/paired-authoring-v1/GAPS.md` records frozen inputs outside the authored
domains. Determine whether the problem contract, input adapter, or candidate
needs correction. Do not rewrite from a title, erase inconvenient cases, or
replace a currently good implementation solely because this older alternative
has an unresolved domain. Later closure for these exact variants was not
established by the accessible records examined here.

### #548, #734, #1788, #2792 — resolve contract/provenance blockers

The first two have unresolved exact official-statement provenance in the legacy
GAPS document. The latter two remain named contract-blocked IDs in the v22
availability receipt. Existing source is still source. None of those flags by
itself establishes a faulty algorithm or a need for new code. Contract acquisition
must use an authorized source; this report does not authorize access bypasses.

### JavaScript #78 — failed alternative, not an unsolved problem

The paired-authoring qualification checkpoint records an adapted alternative
failing strict historical parity while original implementations remain available.
Keep that alternative unused or reconcile/fix the specific comparison contract.
Do not assign another generic Subsets implementation as missing work.

## 4. Repairs already present: do not redo or overwrite

| ID | Languages changed | Current correction |
|---|---|---|
| 68 | JavaScript | Text widths use Unicode code points rather than UTF-16 code units. |
| 2497 | Both | Duplicate undirected edges are ignored before summing neighbors. |
| 814 | Both | Surviving original tree nodes are retained; zero-only links are removed. |
| 2074 | Both | Original linked-list nodes are relinked for even-length groups. |
| 2807 | Both | GCD nodes are inserted between original list nodes. |

These nine corrected source blob IDs account for all three changed authoring
batch tree hashes. `current-blob-overrides.json` records their exact identities.
Do not apply an older downloadable patch in a way that restores its earlier
implementation.

The earlier blanket instruction to preserve every input was too broad. Mutation,
node identity, aliasing, ordering, and arithmetic must follow each actual problem
contract. Uniform naming and layout do not justify changing required effects.

Other repaired historical examples (#1015, #1079, #1088 and the named earlier
#66/#582/#599/#910/#922 repairs) are preserved in
`literals/paired-authoring-v1/QUALIFICATION_STATUS.md`. They are not new blank
source slots merely because an earlier version failed.

## 5. The remaining join, without running solutions

The newer owner report names this local catalogue:

`/home/x/.local/share/gamma-owner-recovery/owner-recovery-20261026/jupiter-current943/catalogue.json`

That report describes 943 paired qualified IDs. The latest committed milestone
registry distinguishes that owner-reported checkpoint from an older locally
verified 518-pair metadata snapshot. Neither is a source-writing denominator.
The actual private catalogue and source locators were not accessible here.

`reconcile_local_inventory.py` reads the supplied metadata-only catalogue and the
included census. Optional source-root enumeration reads filenames and file stats,
not source contents. It does not import Gamma, follow catalogue locators, execute
candidates, read case payloads, or change any approval/qualification status. It
refuses an existing output directory and, when a repository is given, refuses an
output inside that repository.

After extracting the ZIP, run on the machine holding the catalogue:

```sh
python3 reconcile_local_inventory.py \
  --repo /home/x/deco/gamma \
  --catalogue /home/x/.local/share/gamma-owner-recovery/owner-recovery-20261026/jupiter-current943/catalogue.json \
  --output /tmp/gamma-source-backlog-reconciled
```

Add `--source-root` only for an explicitly selected additional directory of
numbered solution files. The reader supports the published metadata-only
catalogue v1/v2 schema. It does not inspect embedded source-bearing corpus files
or automatically infer IDs from arbitrary filenames.

The outputs separate local source files, private catalogue source references,
already-written patches, historical source evidence, and IDs with no source
reference in the supplied inputs. The final residual is a legitimate new-authoring
candidate list only after the operator confirms the supplied inventories cover
all active source locations and checks the existing access classification.

A source-free export is sufficient for remote reconciliation: ID, language,
source path/identity, file availability, and exact failure/source-version binding.
Do not transfer protected tests, expected values, private source text, or query
payloads merely to settle a counting question.

## 6. What this report establishes and does not establish

Established: exact recent source-batch membership, exact current Git-tree matches,
deduplication across all supplied recent patches, specific legacy source evidence,
and retained repair/domain findings tied to named variants.

Not established: universal correctness of existing algorithms, a complete scan
of private source stores, the exact global unwritten count, per-ID classification
of every protected/exterior identity, or a newly passing solution.

The next useful work is **integrate already-written candidates; preserve landed
repairs; resolve the specific resource and contract findings; then assign only
residual missing language slots after the private metadata join**.

## Source references

Unless stated otherwise, repository paths below are relative to
`projects/algorithm_solver/` at `8c0fb7a0971396fcb15b5cd19ddb4b8912f1d946`.

- `catalogue/authored/` — current Git tree metadata, rechecked unchanged at `f9644b354173bd75060673f38a55a63460b1caf3`.
- `catalogue/ALL4081-UNIVERSE-RECEIPT-v3.json` — denominator and exact all-ID hash.
- `literals/paired-authoring-v1/README.md`, `GAPS.md`, `QUALIFICATION_STATUS.md` — development source membership and variant-specific findings.
- `literals/python-devval-v1/README.md`, `manifest.json` — 100 Python candidates and linked JavaScript reference identities.
- `catalogue/authorship-availability-v1/ACTUAL-INTEGRATION-v22.json` — source/contract distinction and retained blockers.
- `catalogue/public-domain-qualification-hard32-wave2-numeric-v2/CHECKPOINT-DEPENDENCIES.md` — original and packed #1743 failures.
- `algsolve/corpus.py` — separate imported Python source collection.
- `catalogue/catalogue.py` and `catalogue/authorship-availability-v1/patch.py` — metadata schema used by the read-only helper.
- `catalogue/MILESTONES.md` at `f9644b354173bd75060673f38a55a63460b1caf3` — explicit 518 verified-metadata versus 943 owner-reported distinction.
- Supplied Medium patches and Library Easy/Hard patches — original source files reconstructed and matched against Git trees.

The JSON files are observations for this audit, not a new canonical Gamma registry.

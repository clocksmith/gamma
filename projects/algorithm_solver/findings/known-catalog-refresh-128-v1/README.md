# Fresh known-answer catalog on x@128

The opt-in candidate catalog now qualifies **2,481 / 3,288 eligible entries**, up from 2,456, with no lost approvals. All 2,481 returned the correct stored source and passed their public examples through the final gated serving path; all 807 eligible exclusions abstained. The 3,353 historical inventory includes 65 present protected aliases, which were excluded before constructing queries or loading tests. This is stored-source/exact-query qualification, not a successful new-description recognition release.

The fresh v2 audit scored every selected stored reference against every available compatible independent set, including references whose public answer path abstained. It found 2,556 independently passing references, of which 75 still fail the public answer path. Across 2,584 independent verdict sets there are 250,898 declared cases and 247,540 recorded passes; failed sets may terminate early, so declared cases are not claimed as executed cases. Approved references passed **241,062 independent tests**. The 25 new approvals passed 2,255. Source/test bytes and provenance are bound; no historical positive verdict authorized an approval. The historical catalog remains unchanged.

## Use the candidate

On128 catalog:

`/home/x/deco/gamma/projects/algorithm_solver/findings/known-catalog-refresh-128-v1/approved-library.json`

From `/home/x/deco/gamma`:

```sh
PYTHONPATH=projects/algorithm_solver OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 MKL_NUM_THREADS=2 \
.venv_rocm/bin/python -m algsolve.answer \
  projects/algorithm_solver/findings/known-catalog-refresh-128-v1/example-query.json \
  --index corpus --fallback none --device cpu \
  --approved-library projects/algorithm_solver/findings/known-catalog-refresh-128-v1/approved-library.json
```

The existing CLI help was checked, and this invocation was executed against the byte-identical run catalog using the supplied `regions-cut-by-slashes` query: `answered`, correct identity, public examples passed. The API is `context, catalog = approved_library.load_context(path)` then `answer(context, query, approved_library=catalog)`.

The manifest explicitly opts into the existing narrow unordered-output contract. Old manifests keep their behavior. The earlier input-record repair remains an offline import correction: the supplied query has repaired original public examples; serving does not silently rewrite user-provided examples. Exact queries load no embedding model. Non-exact inputs use the existing CPU embedding path and have **not** gained a new recognition guarantee. The separate historical 20-known/4-absent release remains 13/20 known versus its 18/20 gate, with 4/4 absent; this work does not promote it or reopen its consumed set.

## Evidence chain and runtime gate

- `runs/catalog-refresh-128-v1` is preserved incomplete: all 3,288 public decisions and 712 classifications. Review found its scorer only tested returned answers, contrary to the protocol's all-reference requirement. It never produced an approval catalog.
- v2 imported only v1's freshly sealed public decisions after proving equality of all serving, query/input, inventory, test-artifact and protected-boundary bindings. Zero independent verdicts were imported. It then freshly scored all 3,288 references in two bounded resumable chunks, and built its immutable original catalog.
- Actual interpreter/bwrap/prlimit and stdlib identities were first recorded **during v2**, not before it. This limitation is explicit in timestamped receipts. The omitted scoring-only `test_corrections.py` binding was separately proven identical to both clean base93075618f and the original frozen library audit, and checked again at completion.
- The final v4 catalog reuses v2's fresh verdicts through an assertion-checked loader-only rebind. Only the existing `approved_library.build` metadata option and `ApprovedLibrary.verify_runtime` gate changed; source selection, identity checks, query parsing, answer path, stored code, tests, test corrections, judge, harness, sandbox and limits did not. All approved/excluded records, counts and policy are identical between v2 and v4. `finalize_catalog.py` records this proof. v3 is preserved unserved; review corrected its identity probe to use the judge's `-I -S` startup before the final v4 verification.
- The optional gate checks fixed local executable paths, resolved targets, interpreter version and 678 stdlib Python/extension source files. A manifest cannot select a command to run. Runtime identities were identical before and after full v4 serving verification. This is intentionally a host-specific qualification, not a portable approval or complete OS/shared-library attestation. All dynamically loaded system libraries and bytecode caches are not separately attested.
- Source/input changes fail closed. `64 tests and 28 subtests passed`, covering runtime drift rejection, manifest policy, independent scoring on public abstention, import-seal drift, judge and lane behavior. A first test command used nonexistent short names for the judge/lane suites; the correctly named repository suites passed in the final run.

The jobs were capped at two CPU threads and 2 GiB under a contended host; observed first-chunk peak was 678,789,120 bytes. No latency promotion is claimed. No model was loaded; no source generation, training, downloads, dependency installation, protected scoring, service interruption, global environment/security change or public push occurred.

`summary.json`, the candidate catalog and compact contracts/receipts are retained here. Full immutable local JSONL evidence stays in `runs/catalog-refresh-128-v{1,2,3,4}`; `artifact-manifest.json` binds every file by size/hash for private preservation. Original v2 evidence is distinguished from the v4 copies and serving run.

## Remaining 807 and next executable work

| Exclusion | Count | Concrete cause / next action |
|---|---:|---|
| Missing independent tests | 685 | Every entry is a single Doocs member with example-only evidence, no hidden path and no same-slug tested source in the eligible normalized corpus. Thirteen have other tested sibling problems; those are not equivalent. Recover a separately sourced/reviewed test corpus or independently authored specifications. Never derive approving tests from the same stored reference or relabel examples as independent. |
| Exact public path | 75 | All selected references independently pass. 61 have public execution/output-contract failures; 14 have no recovered public examples. This is the largest currently supported recovery group. |
| Runtime failure | 26 | 15 need `SortedList`/`sortedcontainers`, 10 hit `MemoryError` under unchanged512MiB judge limits, one lacks a `datetime` import. Limits and runtime imports were not loosened. |
| Unusable imported evidence | 19 | In-place problems whose imported tests only check a `None` return, not mutations. Fresh independently specified mutation checks are required. |
| Unusable checker evidence | 2 | Existing checker/input-domain mismatches remain exclusions. |

The next coherent bounded hypothesis is a **named-output unordered contract**: nine exact-path candidates express permission using nouns instead of literal “the answer” (closest divisors, delete duplicate folders, high-access employees, linked-list frequency, maximum non-overlapping substrings, maximum split, modified graph edges, two-out-of-three, word-break-II). Freeze all nine before decisions, preserve inner order and multiplicity, reject conditional ordering (“any order that satisfies…”), and score against their existing independent tests only after decisions. Some additionally require property or linked-list semantics; nine is the candidate denominator, not a promised gain. Several dozen other cases need problem-specific validity checks rather than an equality relaxation. The 14 missing-public cases split into three parameter-name mismatches, four in-place output forms, four object/API identity adapters, one duplicate Output label, one binary literal and one web-crawler adapter.

For the dependency group, all 27 indexed alternatives across the 15 cases also require SortedList; no existing dependency-free alternate was found. There is **no source version pin**, tracked lock requirement, installed distribution, or named local wheel/cache match. [Sorted Containers2.4.0 on PyPI](https://pypi.org/project/sortedcontainers/2.4.0/) is a concrete proposed version (Apache2, pure Python), not a historically required or already tested version. A future approval must cover reproducible judge-visible packaging/import binding: the judge runs `/usr/bin/python3 -I -S` with read-only `/usr`, so installing into the host venv alone cannot fix it. No install or injection is authorized/performed here.

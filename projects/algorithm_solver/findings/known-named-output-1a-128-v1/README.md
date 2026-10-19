# Named-output candidate: six more usable known answers

The complete frozen nine-case population improved from **0/9 correct to 6/9**, with zero wrong, unqualified or harmful changes. All nine selected references freshly passed 648 independent tests; the six useful answers passed 467. All 18 public decisions were sealed before independent tests were decoded. No protected case, model, generation, new dependency or training was used.

The separate opt-in catalog now has **2,487 approved entries**. Full serving verification through its explicit wrapper returned all 2,487 approved sources correctly and abstained on all 801 eligible exclusions, with zero failures and no encoder loaded. Approved sources carry 241,529 passing independent cases. The previous 2,481-entry catalog remains byte-identical and runtime-valid. This is exact-known-answer coverage, not a new-description recognition release; the separate 13/20 versus18/20 gate is unchanged.

## What changed

`algsolve.named_output_contracts` reads complete unconditional requirement sentences before examples. It recognizes a bounded collection of named output phrases, including paths, integers, values, substrings, sentences and lists of names. It selects the existing outer-list comparator only; it does not change code, expected values, input arguments, inner order, multiplicity, types or explicit caller comparisons. Conditional wording and contradictory ordering requirements fail closed. No key/title/source/example lookup selects the contract.

`algsolve.named_lookup` is a standalone wrapper. Its catalog binds the adapter identity, source hash and wrapper hash, alongside the existing source/test/runtime qualification. Existing `answer.py`, `public_contracts.py`, judge files and all old catalog-bound files were untouched.

Useful cases: closest-divisors; delete-duplicate-folders-in-system; high-access-employees; maximum-number-of-non-overlapping-substrings; two-out-of-three; word-break-II. Remaining cases stayed in the nine-case denominator: linked-list-frequency has unsupported wording/object representation; modify-graph-edge-weights has a conditional clause; maximum-split-of-positive-even-integers allows different valid values requiring a property checker rather than order-only comparison.

## Explicit usage

From `/home/x/deco/gamma`:

```sh
PYTHONPATH=projects/algorithm_solver OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 MKL_NUM_THREADS=2 \
.venv_rocm/bin/python -m algsolve.named_lookup \
  projects/algorithm_solver/findings/known-named-output-1a-128-v1/example-query.json \
  --approved-library projects/algorithm_solver/findings/known-named-output-1a-128-v1/approved-library.json
```

The CLI help and this exact invocation were exercised with closest-divisors: correct identity, `answered`, public examples passed. The API is `context, catalog = named_lookup.load_context(path)` followed by `named_lookup.answer(context, query, approved_library=catalog)`. **The ordinary answer CLI does not automatically enable this adapter.** The wrapper rejects catalogs without its exact adapter binding.

The example query is the unmodified known problem/public input; the wrapper applies the declared output contract automatically. It asks no questions and takes no manual query-time steering. Non-exact requests retain the existing recognition limitations.

## Evidence and checks

The initial v1 candidate and evidence remain preserved. Self-review found missing passive/pronominal contradiction forms; v2 added those checks. Parent review then identified plural obligations, must-not-reorder/must-preserve forms and conditional continuations across line breaks. Final v3 treats newlines as whitespace within sentences and rejects those contradictions. Each correction was frozen and the entire nine-case comparison rerun; all nine query/contract decisions and six successful outcomes are identical across versions. The selected evidence is `corrected-v3/`. The earlier adapter catalog and full serving result are preserved under `superseded-catalog-v1/`; its old adapter hash is intentionally superseded, while the original 2,481-entry catalog remains valid.

`build_candidate.py` chains the complete fresh v4 catalog audit to today's nine fresh candidate/reference verdicts, replacing exactly nine formerly excluded rows and preserving every original approved record. It does not reuse historical pass flags or claim a new full independent rerun. The new complete catalog was built before all 3,288 eligible queries were served through the wrapper; `serving-summary.json` records the result. Runtime identities and source seals were checked before and after. The original catalog remains usable.

The final combined focused/judge/lane suite passed **47 tests and 57 subtests**. Tests cover complete/conditional/quoted/input-only clauses, passive/direct/plural/pronominal contradictions, line-wrap conditions, explicit comparisons, multiplicity, inner order, types, length, adapter mismatch rejection, and actual sandbox execution. The wrapper contradiction test verifies the source itself is still catalog-approved before checking comparison-driven abstention. Jobs were capped at 2 CPU / 2 GiB. Timings are contended development measurements, not latency qualification.

Full local run evidence is preserved under `runs/known-named-output-1a-128-v{1,2,3}` as named in `artifact-manifest.json` and `runs/known-named-catalog-128-v{1,2}`. Compact frozen contracts, scores, catalog and serving proof are included here. Nothing was publicly pushed; no commits were made by this worker.

Remaining eligible exclusions: 685 missing independent tests, 69 exact public paths, 26 runtime failures, 19 unusable imported mutation checks and 2 unusable checker cases. The precise fifteen-case dependency proposal is in `DEPENDENCY_PROPOSAL.md`; it includes a primary-verified wheel digest and a flat task-file/bootstrap plan requiring separate approval, with no download or installation performed.

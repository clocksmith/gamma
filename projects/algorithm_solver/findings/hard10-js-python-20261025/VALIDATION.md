# Validation report

**Date:** 25 October 2026  
**Attempt:** attempt-001  
**Repository conventions pinned at:** `7290ac480db36698b4c69e677f4f51172dd738bd`  
**Gamma qualification:** pending; **0 actual Gamma independent tests executed**.

## Observed results

- **20/20 syntax checks passed:** `node --check` and Python `py_compile`.
- **50,283/50,283 paired local cases passed** in both languages.
- **50,268 cases** are within the public problem domains; **15** are separately labelled empty-input/zero-k extension probes.
- **201,132 candidate calls:** canonical plus native entry point in each language. This is not that many distinct tests.
- **50,283 canonical JavaScript/Python output agreements**.
- **201,132 per-call input-content and nested-container-identity checks** passed.
- **0 failing candidate outcomes** in the retained behavioral attempt. No repairs or discarded failing candidate receipts were needed.

| ID | Paired cases | Normative cases | Public examples | Largest-input checks | Status |
|---|---:|---:|---:|---:|---|
| 10 | 8,153 | 8,148 | 3 | 0 | Passed locally |
| 42 | 6,067 | 6,066 | 2 | 4 | Passed locally |
| 84 | 4,412 | 4,411 | 2 | 4 | Passed locally |
| 85 | 1,191 | 1,189 | 3 | 4 | Passed locally |
| 123 | 5,868 | 5,867 | 3 | 4 | Passed locally |
| 546 | 3,487 | 3,486 | 3 | 4 | Passed locally |
| 564 | 6,080 | 6,080 | 2 | 0 | Passed locally |
| 992 | 6,412 | 6,410 | 2 | 5 | Passed locally |
| 1074 | 3,003 | 3,002 | 3 | 6 | Passed locally |
| 1187 | 5,610 | 5,609 | 3 | 6 | Passed locally |

## Case categories

- analytic_stress: 37
- boundary: 83
- exhaustive_oracle: 45,122
- metamorphic: 650
- outside_domain_extension: 15
- public_example: 26
- randomized_oracle: 4,350

## Exactly what ran

`validation/build_cases.py` generated a fixed-seed corpus, checked normative input bounds, and cross-checked the large-number palindrome oracle against independent brute-distance results on 1..5000. `validation/validate.py` syntax-checked all sources and launched one JavaScript and one Python input-only worker per problem. Every worker exercised both API entry points on each case. All outputs and worker standard errors are retained under `validation/attempt-001/`.

The references are not identical cross-language copies used as an oracle: separate simpler algorithms provide the expected answers. Case inputs and expected results are bundled for reproducibility. No actual Gamma test cases, hidden LeetCode tests, private problem contracts, or benchmark verdicts were obtained or run.

## Runtime and limitations

- Node.js: `v22.16.0`; no special Node flags.
- Python: `3.13.5 (main, Jul 15 2026, 20:25:40) [GCC 14.2.0]`.
- Platform: `Linux-6.18.55-x86_64-with-glibc2.41`.

These checks ran in ordinary local worker processes, not the pinned Gamma bubblewrap sandbox. Executable hashes, source hashes, case hashes, counts and timings are in `validation/latest-report.json`. Exact native Gamma runtime and frozen-contract qualification remains for the coordinator. Finite tests and mathematical outlines are not a formal proof or an independent laboratory attestation. No performance superiority or novel algorithm claim is made.

## Packaging checks

The final ZIP is checked for exactly 10 selected JavaScript IDs, the same 10 Python IDs, 20 six-field semantics records, 10 contract summaries, and all expected validation/provenance files. Every payload hash is verified after extracting the ZIP. The checksum manifest excludes only itself to avoid a circular hash. See the separate archive-verification JSON beside the download.

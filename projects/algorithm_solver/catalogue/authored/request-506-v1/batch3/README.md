# Batch 3: 61 original candidate pairs

Base: `62f8d1e2b375ab1c576a412be06adeddb5bcbffe`.
`manifest.json` binds each ID to exact source URLs, contract/adapter notes,
complexity, candidate hashes and development-case counts. All 61 assigned IDs
have JavaScript and Python candidates. None is admitted, independently qualified,
or represented as a hidden-judge accepted solution.

Run from this directory (Python 3.11+, Node 18+):

```
PYTHONDONTWRITEBYTECODE=1 python test_candidates.py
PYTHONDONTWRITEBYTECODE=1 python test_triangle.py
PYTHONDONTWRITEBYTECODE=1 python test_native_interfaces.py
```

Observed: 2,101 checks in each language: 2,042 main examples/oracles, 50
independent triangle simulations, and 9 native-interface fixtures. Main oracles
use seed 3061. Triangle includes n=1000 with Node heap capped at 256 MiB; its
queue simulation is O(n²). Result JSONs report measured durations, not performance
qualification. Production-scale runtime was not evaluated for every candidate.

## Interfaces and numerical details

- Stateful exercises use `solve(operations, arguments)`, constructor first,
  official method names, and null/None for void returns. 2102 uses an offline
  coordinate-compressed call-array adapter but only counts previously added items.
- 1973 and 3157 explicitly accept compact BFS tree arrays with null children.
- 2046 supports native `{val,next}` / attribute nodes, preserving identity and
  reordering links in place. Array input is an explicit values-only serialization.
- 2773 supports native special tree nodes with reciprocal circular leaf links.
  Array input explicitly serializes the underlying tree before circular links.
- 2941 uses exact Python integers and returns JavaScript BigInt above
  `Number.MAX_SAFE_INTEGER`; transport such output as an integer decimal string.
  Its inputs remain safely representable JSON numbers. Never coerce its large
  answer to Number. 2557 and 3180 also use BigInt intermediates internally.
- 2117 uses exact products; Python leading-digit extraction avoids the interpreter's
  full integer-to-decimal string limit. Both runtimes tested right=10000.
- 2647 has a separately documented original optimal construction and independent
  activation test. 2664 uses complete Warnsdorff-ordered backtracking, exponential
  worst-case complexity; bounded tests do not establish worst-case latency.

## Provenance and boundary

Official public definitions and identity-bound public doocs/leetcode definition
sections were read; no editorial code was copied. Supplementary definition docs
are CC-BY-SA-4.0; their exact excerpt hashes and URLs are in the manifest, not
redistributed full statements. The pre-open existing boundary gate was used;
`boundary-recheck.json` is explicitly a subsequent metadata-only recheck, not
an acquisition timestamp or semantic verification receipt. No protected cases,
judge submission, admission registry update, commit or push occurred.

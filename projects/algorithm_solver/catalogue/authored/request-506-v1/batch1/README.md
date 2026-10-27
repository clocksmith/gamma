# Batch 1: 61 paired authored candidates

Base: `62f8d1e2b375ab1c576a412be06adeddb5bcbffe`. All 61 IDs passed the existing pinned pre-open boundary authorization; receipts are in `authorization.json`. No reserved cases or hidden judges were read or executed.

Run from repository root:

```sh
python projects/algorithm_solver/catalogue/authored/request-506-v1/batch1/run_tests.py
```

Result: 2,254 cases × two languages = 4,508 passing assertions. Every ID has documented examples and independently derived bounded oracle cases. Cross-language agreement is not counted as an independent oracle. Both implementations were checked against independently computed expectations. JavaScript syntax and Python compilation also passed for all 61 pairs. Detailed per-ID case categories are in `test-results.json`; source hashes, arguments, complexity and source URLs are in `manifest.json`.

Sources are official problem contracts, with 19 premium definitions grounded in the public doocs statement-only mirror (CC-BY-SA-4.0, attributed per ID). Implementations are original; no editorial implementation was copied. No raw statement corpus is included.

Stateful designs use explicit operations/arguments tapes. Node problems take native `.val`, `.next`, `.left`, `.right` objects; arrays are test transport only, not a new solver contract. 2901 tests accept any valid maximum-length subsequence, not just one reference output.

Limitations: these are authored, locally tested candidates, not admitted or scientifically qualified results. Independent oracles use small bounded inputs. Full constraint-scale performance, hidden-judge behavior and integration qualification remain untested. No protected confirmation campaign or admission registry was changed.

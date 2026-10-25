# Incremental family vocabulary baseline

This is the first completed systematic growth/merge ledger, not an M1 success.
It uses 300 development-fit problems and 466 independently qualified JavaScript
source variants. The 128-entry result is 57,389 selections, median 149, p95 389,
72.32% character bits and 71,580 complete package-plus-decoder bytes.

Independent review checked all 300 ledger events, 31,388 event/problem
measurements, source reselection, complete costs and final packets. No orphan
cost records were present. `results-summary.json` holds aggregate proof hashes.
The original slow and accelerated engine receipts remain unchanged.

The failure is informative: 32 learned strings total only 78 bytes, so retaining
all intermediate fragments saturates capacity before longer compositions grow.
The linked `../incremental-merge-v2/` continuation composes adjacent pieces while
retiring obsolete learned parents at the same budget. It does not reset the
dictionary or make an impossibility claim. All500 M1 thresholds remain unchanged.

The historical v1 accelerator loads its owned compiler artifact at import;
although its actual artifact hash matched and exact DP checks passed, use the
v2 pre-load hash-checked loader for new work. The initial v1 identity did not pin
every transitive scoring dependency; v2 explicitly pins those dependencies too.
These limitations are preserved rather than silently editing old contracts.

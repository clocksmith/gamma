# Development checks

- `python3 .../macro-fragment-compare-v1/test_codec.py`: 13 passed. Covers
  exhaustive short-string segmentation, exact Unicode/integer bytes, nested
  operands, CONCAT overhead at each width, count words, noncanonical packets,
  whole-body/class exclusions, duplicate-source reuse and original-body bans.
- `python3 -m pytest -q tests/test_algorithm_solver_judge.py tests/test_algorithm_solver_lane.py`:
  10 passed, 27 skipped. The skipped tests require Linux bubblewrap/prlimit,
  unavailable on this host. No candidate execution bypassed that requirement.
- Changed Python files compile; `node --check js_shapes.cjs` passes.
- Python 3.13.2 and Node v22.20.0 on macOS; JavaScript AST inspection uses
  Node's bundled Acorn with ECMAScript 2022 parsing.
- `python3 tools/catscan.py --check` validates the charters but reports a
  pre-existing stale generated component index: its WGSL training campaign row
  is missing. That unrelated generated index was not changed by this experiment.

The completed packet replay is recorded separately in
[verification.json](verification.json). Its counts include both primary
languages and the separately unqualified compact-Python diagnostic.

All three private attempts are retained under
`/Users/xyz/.cache/gamma-macro-fragment-20261109-v{1,2,3}`. The final report links
the second report by hash, and that report links the first. Earlier implementation
snapshots remain beside their artifacts. No private source, codebook or packet
was committed.

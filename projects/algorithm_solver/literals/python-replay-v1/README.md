# Python development qualification

Python is an independent M1 lane. The frozen population is still 500, with only
400 development problems currently authorized. Final 100 and protected 66 remain
closed. **Python M1 is not achieved.**

## Existing evidence, 2026-10-25

Independent replay of retained paired Python observations established current
source return/effect/alias parity on **234 authored fit programs, 23,625 cases**.
This is JSON-interface evidence, not typed-interface coverage and not a 400-program
claim. All 300 authored fit programs had earlier attempts; 35 remained unsupported
or domain-blocked, and 31 failed. Three optimized runtime successors and eight
subsequent effect/output-order successors require their own fresh Python replay.
The authored inventory itself is not correctness evidence.

Private proof: `python-paired-observation-review.json` (hash-bound observations and
source-linked report inventory retained outside the repository). No private case,
original implementation, output or trace is published here.

## New executable step

`qualify.py freeze` seals complete authored Python sources and semantics before
`qualify.py run` executes them through the unchanged sandbox. `verify.py` separately
replays every retained raw observation and derives eligibility; flags alone do not
admit a source. See [CONTRACT.md](CONTRACT.md) for the explicit cross-language
behavior-specification bridge, Python numeric/type semantics and limitations.
Expected outputs never enter the sandbox. Historical JavaScript runtime passes
are not transferred to Python.

The 12 synthetic transport/comparator tests cover typed nodes, mutation aliases,
exact integers, bool/int distinction, unsupported containers, unsafe floats,
cycles, scalar type mapping, output parity and process-failure retention. They do
not execute any submitted candidate or replace native isolated qualification.

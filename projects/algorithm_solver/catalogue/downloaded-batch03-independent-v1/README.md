# Downloaded third batch: unexecuted qualification preparation

This lane prepares independent checks for 88 selected problem IDs, comprising176
exact supplied JavaScript/Python programs from `authored/downloaded-general88-v1`.
**This delivery establishes zero physical candidate executions and zero
independently qualified programs.** Its 1,512 cases are prepared reference
inputs and expectations, not observed candidate passes.

The original `delivery/report.json` says `execution_status: unexecuted` and
`passed: false`. The original `delivery/replay.json` verifies preparation hashes
and case regeneration; it does not replay physical candidate observations.
The corrected [results](RESULTS.md) and hash-bound
[evidence classification](EVIDENCE-CLASSIFICATION-20261028.json) supersede the
unsupported public summary, without rewriting original delivery artifacts.

## Source and interface scope

The original candidate bytes, immutable import manifest and authoring identities
remain unchanged. Historical protected Gamma sources, statements and cases stay
closed. No catalogue admission, activation or retrieval slot changes follow.

Future checks would call the supplied positional `solve` entrypoints. Ten
problems26,27,31,48,73,75,80,88,130 and186 have functional return-value adapter
contracts distinct from their official in-place or length-return APIs. Their
unchanged-on-return inputs, full typed outputs and fresh mutable results still
need physical observation. Neither those effects nor the official wrappers are
execution-qualified by this delivery.

## Comparator and source-review limitations

The corrected unordered routes retain recursive JSON types, container shape and
multiplicity while ignoring only allowed ordering. Integer/bool/float values do
not collapse into each other. Gray Code 89 now checks an exact positive integer
bit width and exact integer values in `[0, 2**n)`, alongside its retained length,
zero start, uniqueness, adjacency and cyclic-closure predicates. Predicate373
checks available index-pair multiplicity and the optimal sum threshold while
allowing legitimate ties and repeated values supported by distinct indices.
These are host checks; they do not establish candidate execution or complexity.
See [the comparator review](REVIEW-20261028.md) for exact historical defects.
Other existing policies, including 50's floating-point tolerance, remain scoped
to their original contracts rather than being promoted into broader acceptance.

Mandatory source-review failures for 41,164 and 373 in both languages remain in
`oracles.MANDATORY_FAILURES`. Their six failure identities are neither observed
candidate test failures nor evidence that the other 170 programs qualify.
Definition 186 remains premium/unavailable in the retained pins. Prepared local
examples cannot clear its official-definition gate. All other source, domain,
interface, effects and complexity obligations still require exact review.

## Existing isolated execution protocol

The target remains the existing Linux bubblewrap judge with private namespaces,
no network, restricted mounts and unchanged bounds: three CPU seconds, eight
wall seconds, 1 GiB address space and 16 MiB output. Each interpreter batch repeats
its first call to check carryover. Sources, observation transport and argument
packets enter the sandbox; expected values and statement snapshots stay on the
host. Missing isolation has no unsandboxed fallback.

The retained freeze was produced on macOS, where `/usr/bin/bwrap` was absent.
Its metadata and all original delivery files remain historical preparation
artifacts. The corrected helper/documentation bytes require a new reviewed
freeze before execution. A future authorized Linux run must bind actual source,
interface, definitions, cases, helpers, runtime and limits, retain raw failures,
and undergo independent stricter host replay. Generated or synthetic records
cannot substitute for physical candidate observations. All adoption eligibility
remains pending those steps; no wrapper, held-out or official judge claim is made.

Source-free development checks are `python3 -B test_oracles.py` from this
folder and scoped Ruff. They test reference/validator behavior and the existing
verifier's unexecuted metadata branch; they execute no candidate programs.

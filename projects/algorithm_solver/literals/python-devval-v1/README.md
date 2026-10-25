# Python development-validation source freeze v1

Owner: [Algorithm Solver charter](../../CATSCAN.md).

This inventory supplies 100 newly authored standalone Python `solve` candidates
for exactly the already-approved development-validation partition. It complements,
but does not replace or edit, the 300 development-fit candidates in
[paired-authoring-v1](../paired-authoring-v1/README.md).

## Frozen inputs and complete source

[manifest.json](manifest.json) binds the exact IDs, UTF-8 source bytes, semantic
sidecars, selected permitted JavaScript reference source hashes, and the prior
joint-freeze and filtered-metadata commitments. The original imported sources
are not copied into this inventory. Each `.py` includes its complete entrypoint,
helper definitions, constructors and explicit standard-library imports. There is
no implicit `TreeNode`/`ListNode`, JavaScript runtime/source channel, generated
implementation, problem-specific hidden helper or uncharged adapter.

The programs were independently written as Python algorithms after inspecting
only the exact permitted selected reference sources. This is not a claim of
independence from reference-source semantic information. No candidate algorithm
was imported or executed, no validation case/expected payload was read, and no
validation literal-cost feedback was used during authoring. Static verification
uses `ast.parse`, inventory/partition checks and source hashes only.

## Effects and unresolved domains

Each semantic sidecar declares input/return shape, numeric assumptions,
mutation/aliasing and actual algorithmic complexity. Effects are not uniformly
pure: 41 cyclically permutes its input, 92 relinks original nodes, 57 returns
untouched original interval rows, 1167 reduces the original stick list, and 1168
appends well edges and stable-sorts the original pipes list. 105, 109 and 2181
include fresh node constructors. Alternate valid outputs are not automatically
substituted for deterministic reference choices.

The imported filtered metadata and reviewed sources do **not** supply a complete
normative domain and complexity contract. Therefore these domain declarations
are provisional author claims, not a replacement for a frozen contract. The
sidecars explicitly flag unusual empty/negative-index/numeric extensions where
relevant. Out-of-domain behavior is unresolved, not guessed from validation
outputs. Compatibility tests can establish only observed source-bound parity;
they cannot turn an undefined domain into normative correctness.

## Next gate

Independent source-bound isolated judging must use the frozen host oracle and
check return types, effects, aliases, numeric and complexity obligations while
keeping expected outputs outside the sandbox. Preserve the first frozen source
and any rejected attempts if later candidates are needed. No source count or
syntax pass constitutes admission or milestone completion.

These sources are **unqualified candidates**. The M1 denominator remains 500,
the thresholds stay unchanged, and neither final-heldout100 nor protected66 was
opened. The inventory adds no dictionary fit, live deployment or protected-score
authority. Source-only authoring does not establish M1 or M2.

# Target Layout Decisions

This is a decision record, not an instruction to move files. It separates the
desired user-facing ownership from implementation details that a migration
script must know exactly.

## Approved Boundary

| Current root | Target root | Status | Ownership |
| --- | --- | --- | --- |
| `content/physical/` | `physical/` | Confirmed | Authored copy and specifications that ship with the physical game. |

## Execution Constraints Already Known

| Boundary | Required preparation before its move |
| --- | --- |
| `content/physical/` | Extend the content compiler and graph source-root policy to admit `physical/`; update every graph source path in the same migration. |
| `prototype/` | Update browser entry points, server routes, package commands, generated HTML targets, and documentation links. |
| `simulation/` | Update browser module URLs, CLI commands, imports, report paths, and documentation links. |
| `dist/` | Confirm every renderer and publisher treats the renamed directory as generated output. |
| `versions/` | Do not move in this migration; historical bundles remain byte-for-byte intact. |

## Decisions Required

| Current root | Candidate target | Missing decision |
| --- | --- | --- |
| `prototype/` | `web/` | Confirm that the browser surface should be named for its delivery medium rather than its prototype maturity. |
| `simulation/` | `lab/` | Confirm that simulation, policies, experiments, and their contracts share one lab boundary. |
| `tools/`, `scripts/` | One shared command boundary | Select separate literal destinations and subfolders. Do not merge them blindly: each command needs a stable invocation path or compatibility shim. |
| `studies/`, `playtests/` | One evidence boundary | Select separate literal destinations beneath the parent and preserve observed-play and simulated-study identities. |
| `dist/` | `build/` | Confirm rendered outputs are disposable build products and document any checked-in exceptions. |
| `data/` | undecided | Choose whether generated runtime projections remain a first-class top-level boundary. |
| `content/runtime/` | undecided | Choose whether authored runtime copy belongs with the browser, the lab, or a shared content boundary. |
| `content/deferred/` | undecided | Choose whether optional physical modules belong under `physical/optional/` or remain a separate authored-content boundary. |
| `versions/` | unchanged | Historical snapshots are immutable evidence. Any later archive rename requires a new snapshot and an explicit policy decision. |

## Apply Contract

An execution map must replace every prose row with one source directory and
one destination directory. It must also name compatibility shims, generated
directories to rebuild, and every command/import/documentation reference that
changes. No migration script may infer those choices from folder names.

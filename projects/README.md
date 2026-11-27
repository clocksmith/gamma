# Gamma projects

Each project owns its code, inputs, tests, and run records. Shared model tooling
lives in [Gamma](../gamma/) and [Gamma Core](../gamma-core/). Independently built
applications are listed in [apps](../apps/README.md).

| Project | Start here |
| --- | --- |
| [Algorithm Solver and BITS](algorithm_solver/README.md) | Qualified programs, the authored catalogue, and vocabulary experiments. Run the local pytest contracts from the project directory. |
| [Distillation](distillation/README.md) | Translation, embedding and WGSL studies, with shared data preparation under `distillation/shared/`. The old [EmbeddingGemma path](embeddinggemma_subsets/README.md) holds compatibility commands and retained inputs. |
| [Reconfiguration](reconfiguration/README.md) | Request-conditioned mechanisms and their frozen study contracts. Run the local pytest contracts. |
| [Self-transform](self_transform/README.md) | Versioned Node experiments and Python neural-proposer studies. The family index lists each version and its CPU checks. |
| [B-track diagnostics](b_track_diagnostics/README.md) | Receipt audits and development controls for the B1 and B2 studies. |
| [SAME-R](samer/README.md) | Matched capability-transfer protocols, domain adapters and experiment records. |
| [Workspace](workspace/README.md) | Browser observation, action, workflow reuse and recovery. Stock Chrome is the default, with optional pinned Fawn integration. |
| [Shared study catalogue](problem_catalogue/README.md) | Cross-repo schema and migration tools. |
| [Question bank](question_bank/README.md) | Source inventories for interview and programming problems. |
| [enwiki9](enwiki9/README.md) | Archived compression research and [retained-output restoration](enwiki9/docs/archive-maintenance/README.md). |

The Python test entry points run from a source checkout with adjacent inputs.
Check each project's README for dependencies and reproduction instructions.

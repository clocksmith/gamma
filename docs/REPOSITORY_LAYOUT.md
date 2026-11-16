# Gamma code and retained evidence

`gamma/` is the importable model toolkit. `gamma.py` remains a compatibility
launcher; `python -m gamma` and the installed `gamma` command use the same
implementation. Backend dependencies and provisioned model weights remain
separate from source installation.

```bash
python3 -m pip install ./gamma-core .
python3 -m gamma help
```

The independently packaged `gamma-core/` supplies shared engine/game/UI
primitives. Install an appropriate backend separately, for example the
toolkit's `pytorch` extra. No packaging or layout check downloads model weights.
Built-in Mind Meld presets ship in `gamma/mind_meld/configs/`. User model files
and generated reports belong to the working directory, not site-packages;
`GAMMA_WORKSPACE` explicitly selects the model workspace when needed.

The Python CLI implementations now live in `gamma/commands/`. Their original
`tools/*.py` scripts remain launchers. Node code-generation benchmarks remain a
separate checkout tool at `tools/codegen-bench/`, with their own dependencies;
they are not part of the Python wheel.

`projects/` contains independent research projects. Their local front doors
describe tests, resources and reproduction requirements. Package metadata does
not imply a self-contained wheel: Algorithm Solver needs its adjacent catalogue
and contracts, while distillation and reconfiguration retain different pipelines
and frozen mechanisms. Active experiments retain their own namespaces.

`apps/` contains the game, web client, MCP server and Flux. Flux's `src` package
belongs to Flux; it is not the toolkit's former `src` namespace. The toolkit's
Python wheel excludes all applications, research projects and run output.

The self-transform family keeps distinct experiment directories and versions
under `projects/self_transform/`; mechanisms and sealed evidence are not merged
into interchangeable configurations.

Current commands and navigation use the new paths. The separate relocation map
records original prefixes; historical receipts, source revisions, digests and
path strings remain evidence of the original run. It does not rewrite them.
Original versions remain available at the map's published source revision.

The [enwiki9 pilot](../projects/enwiki9/docs/archive-maintenance/README.md)
separates verified retained outputs from maintained source. Its catalog records
original paths, immutable commit URLs, Git blobs, SHA-256, sizes and modes. A
fresh GitHub clone restored and CPU-verified the selected outputs before their
tracked copies were removed. Original JSON receipts and required fixtures stay
tracked. Unresolved output-looking files, authored catalogue entries and corpora
are preserved pending their own classification and restoration checks.

Published Git history is the first retention backend. This reduces the current
tree only; it does not reduce existing history or full-clone size, and it is not
locked object storage. Any future history purge must migrate and independently
verify every retained object first. This refactor does not authorize a purge.

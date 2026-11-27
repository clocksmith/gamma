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
they are not part of the Python wheel. Installed commands can select that
checkout with `GAMMA_WORKSPACE`. Its maintained report generator lives in
`tools/codegen-bench/reporting/`, separate from ignored generated `reports/`;
the relocation map records the original recovered source revision.

`projects/` contains independent research projects. Their local front doors
describe tests, resources and reproduction requirements. Package metadata does
not imply a self-contained wheel: Algorithm Solver needs its adjacent catalogue
and contracts, while distillation and reconfiguration retain different pipelines
and frozen mechanisms. Active experiments retain their own namespaces.

[Apps](../apps/README.md) has one directory per runnable application, including
[Mandate 2038](../apps/mandate-2038/README.md). The toolkit wheel includes
`gamma/`; each application packages its own source and resources.

The [self-transform family](../projects/self_transform/README.md) contains the Node
and Python studies in sibling version directories. Each version owns its
implementation and protocol.

The [relocation map](path-relocations-20261116.json) records earlier paths and
the revisions where they existed. Historical receipts preserve the original
paths, source revisions and digests.

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

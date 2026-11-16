# Distillation projects

This checkout owns three separate areas:

- [Translation](translation/README.md): paired-data training, evaluation and promotion.
- [Embedding](embedding/README.md): embedding datasets, training and evaluation.
- [WGSL](wgsl/README.md): shader data, verification and adaptation.

`shared/` owns common record validation. Translation scripts also import through
`projects.distillation` and resolve Gamma and adjacent dataset/run paths. The
local `pyproject.toml` configures tests; it does not claim these resources or all
training dependencies form a portable wheel. Keep the source layout, manifests
and sealed result paths intact.

From this directory, run focused CPU decision/rule controls:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -B -m pytest -p no:cacheprovider -c pyproject.toml
```

These tests do not launch training, evaluate a model or establish promotion.
Use each area's README for explicitly requested runs and dependencies. Keep
training/evaluation output separate from reporting rebuilds.

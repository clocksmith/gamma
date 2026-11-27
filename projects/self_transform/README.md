# Self-transform studies

The Node studies and Python neural-proposer studies live here as sibling
versions. Each version owns its operator, tests and protocol.

## Tests

From this directory, `npm test` runs all ten original CPU tests from a foreign
working directory. Each study also supports `npm test` locally. No dependency
installation, GPU, model download or study execution is required.

## Python neural-proposer studies

| Version | CPU tests from the Gamma root |
| --- | --- |
| [v1](self_transform_neural_proposer_v1/README.md) | `python -m unittest projects/self_transform/self_transform_neural_proposer_v1/test_neural_proposer.py` |
| [v2](self_transform_neural_proposer_v2/README.md) | `python -m unittest projects/self_transform/self_transform_neural_proposer_v2/test_proposer_v2.py` |
| [v3](self_transform_neural_proposer_v3/README.md) | `python -m unittest projects/self_transform/self_transform_neural_proposer_v3/test_proposer_v3.py` |
| [v4 development](self_transform_neural_proposer_v4_dev/README.md) | `python -m unittest projects/self_transform/self_transform_neural_proposer_v4_dev/test_identity_v4dev.py` |

Use a Python environment with PyTorch. These tests exercise CPU control paths.

## Node studies

| Version | Focused command from Gamma root |
| --- | --- |
| [self_transform_curvature_v1](self_transform_curvature_v1/README.md) | `node projects/self_transform/self_transform_curvature_v1/test.mjs` |
| [self_transform_secant_regen_v1](self_transform_secant_regen_v1/README.md) | `node projects/self_transform/self_transform_secant_regen_v1/test.mjs` |
| [self_transform_subspace_v1](self_transform_subspace_v1/README.md) | `node projects/self_transform/self_transform_subspace_v1/test.mjs` |
| [self_transform_v1](self_transform_v1/README.md) | `node projects/self_transform/self_transform_v1/test.mjs` |
| [self_transform_v2](self_transform_v2/README.md) | `node projects/self_transform/self_transform_v2/test.mjs` |
| [self_transform_v3](self_transform_v3/README.md) | `node projects/self_transform/self_transform_v3/test.mjs` |
| [self_transform_v4](self_transform_v4/README.md) | `node projects/self_transform/self_transform_v4/test.mjs` |
| [self_transform_v5](self_transform_v5/README.md) | `node projects/self_transform/self_transform_v5/test.mjs` |
| [self_transform_v6](self_transform_v6/README.md) | `node projects/self_transform/self_transform_v6/test.mjs` |
| [self_transform_v7](self_transform_v7/README.md) | `node projects/self_transform/self_transform_v7/test.mjs` |

## Reproduction boundaries

Existing sibling imports still resolve within this family. Runners locate their
workers and protocols through `import.meta.url`; source-hash keys and exclusive
output creation remain intact. Error/usage strings inside frozen modules may
show historical paths; the [relocation map](../../docs/path-relocations-20261116.json)
connects them to the current layout. Keep full sibling closures for v2-v7 and curvature reproductions.
Use each study README for explicit run/selection/confirmation commands and fresh
output paths. Historical receipts retain their original identifiers and paths.

# Self-transform studies

The ten tracked studies now live together; their version names and measured
source/protocol bytes are unchanged. This is a Node ESM family, not a Python
package or one configurable replacement mechanism. The active untracked neural
proposer studies were not moved.

## Tests

From this directory, `npm test` runs all ten original CPU tests from a foreign
working directory. Each study also supports `npm test` locally. No dependency
installation, GPU, model download or study execution is required.

## Path map and current commands

| Previous directory | Current directory | Focused command from Gamma root |
| --- | --- | --- |
| `projects/self_transform_curvature_v1/` | [self_transform_curvature_v1](self_transform_curvature_v1/README.md) | `node projects/self_transform/self_transform_curvature_v1/test.mjs` |
| `projects/self_transform_secant_regen_v1/` | [self_transform_secant_regen_v1](self_transform_secant_regen_v1/README.md) | `node projects/self_transform/self_transform_secant_regen_v1/test.mjs` |
| `projects/self_transform_subspace_v1/` | [self_transform_subspace_v1](self_transform_subspace_v1/README.md) | `node projects/self_transform/self_transform_subspace_v1/test.mjs` |
| `projects/self_transform_v1/` | [self_transform_v1](self_transform_v1/README.md) | `node projects/self_transform/self_transform_v1/test.mjs` |
| `projects/self_transform_v2/` | [self_transform_v2](self_transform_v2/README.md) | `node projects/self_transform/self_transform_v2/test.mjs` |
| `projects/self_transform_v3/` | [self_transform_v3](self_transform_v3/README.md) | `node projects/self_transform/self_transform_v3/test.mjs` |
| `projects/self_transform_v4/` | [self_transform_v4](self_transform_v4/README.md) | `node projects/self_transform/self_transform_v4/test.mjs` |
| `projects/self_transform_v5/` | [self_transform_v5](self_transform_v5/README.md) | `node projects/self_transform/self_transform_v5/test.mjs` |
| `projects/self_transform_v6/` | [self_transform_v6](self_transform_v6/README.md) | `node projects/self_transform/self_transform_v6/test.mjs` |
| `projects/self_transform_v7/` | [self_transform_v7](self_transform_v7/README.md) | `node projects/self_transform/self_transform_v7/test.mjs` |

## Reproduction boundaries

Existing sibling imports still resolve within this family. Runners locate their
workers and protocols through `import.meta.url`; source-hash keys and exclusive
output creation remain intact. Error/usage strings inside frozen modules may
show historical paths; use the mapped directory above rather than rewriting
measured code. Keep full sibling closures for v2-v7 and curvature reproductions.
Use each study README for explicit run/selection/confirmation commands and fresh
output paths. Historical receipts retain their original identifiers and paths.

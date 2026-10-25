# Existing informal-recognition asset readiness

This is a prerequisite inventory for goal1b, not a new model choice, encoder run,
training job, threshold fit or recognition result. The exact-ID CLI works without
these assets. Use `recognition_assets.py` in the **actual serving namespace**:

```sh
python3 -m projects.algorithm_solver.catalogue.recognition_assets \
  --lane-root /workspace/shared/deco/gamma/projects/algorithm_solver \
  --output /approved/recognition-assets-native.json
```

The probe inspects exactly five model-side paths and four index paths, plus
installed-distribution metadata for torch, transformers, numpy, safetensors and
tokenizers. It imports none of those packages, opens no candidates/cases, does not
load arrays/encoders, scans no directories, dumps no environment and downloads
nothing. Default behavior stats weights/tokenizer/indexes and hashes only the
three small auxiliary files (16MiB maximum each). Optional
`--verify-model-hashes` streams only the two explicitly pinned files for SHA256;
it still does not instantiate a model. Do not use that option merely to discover
whether a missing file exists.

## Exact root resolution

Immutable public `algsolve/embed.py`, commit
`32b0e46bc2909cde11659bc2927737791a4a28a1`, blob
`c78d3de57d6f92bc529dd380603348e5eab0a280`, uses:

1. `ALGSOLVE_EMBEDDING_DIR` if present; no other environment variable is inspected
   by this readiness probe.
2. Otherwise the literal default
   `/home/x/.local/share/doppler/capsule-baselines/20260906/source-checkpoints/qwen-embedding-source-97b0c614`.

The pinned implementation calls `Path(...)` without `expanduser()`, automatic
snapshot discovery or a second model location. An unset variable is different
from an empty one. A `~` value is not shell-expanded when set as environment text.
Use an explicitly approved absolute path when provisioning the actual serving
namespace; do not silently search other user homes or caches.

## Required assets and provenance

Repository/model identity is `Qwen/Qwen3-Embedding-0.6B` with these exact pins:

| Exact filename | Required SHA256 |
| --- | --- |
| `model.safetensors` | `0437e45c94563b09e13cb7a64478fc406947a93cb34a7e05870fc8dcd48e23fd` |
| `tokenizer.json` | `def76fb086971c7867b829c23a26261e38d9d74e02139253b38aeb9df8b4b50a` |

`config.json` and `tokenizer_config.json` govern AutoModel/AutoTokenizer behavior;
`special_tokens_map.json` is an optional auxiliary asset whose presence/absence
must be recorded. The legacy module does not pin hashes for these files. The
probe records observed hashes but deliberately does not mark them verified:
matching an independently approved original snapshot is still required. Do not
invent auxiliary hashes from a current upstream release. Additional package-
specific asset requirements must be established against the actual frozen runtime,
not obtained by allowing `from_pretrained` to fetch missing pieces.

The legacy approved library binds serving Python code, judge files, run and
threshold contracts, index artifacts and an optional runtime-environment manifest.
Record exact Python executable/version and installed package versions first;
package metadata presence does not prove importability or numerical equivalence.
A complete frozen runtime/file hash manifest and matching index/encoder provenance
remain necessary. The run contract's generative-model ROCm backend string is not
proof of the CPU recognition runtime version.

Exact corpus index paths under the supplied lane root:
`data/derived/corpus_embeddings.npy` and
`data/derived/corpus_embedding_keys.json`. The separately inspected research
alternatives are `index_embeddings.npy` and `index_embedding_keys.json`; they are
not substitutes for the corpus population. No array payload is read in the
readiness probe. Source-free key/identity metadata, exclusion closure and vector
order/hash bindings must be supplied independently; do not read the legacy
source-bearing corpus entries to establish them.

## Observed sparse-exec namespace

The checked Python was
`/opt/codex/runtimes/codex-primary-runtime/dependencies/python/bin/python3`,
version3.12.14. `ALGSOLVE_EMBEDDING_DIR` was absent. All five exact model-side files
and all four exact index paths were absent. Package metadata showed numpy2.3.5;
torch, transformers, safetensors and tokenizers were not installed in this Python.
No model/index file size was verified, so no asset size or transfer estimate is
claimed. This says nothing about another namespace on the same computer.

The native-dot probe is required before concluding the assets need provisioning.
If those exact native paths are also absent, the concrete blocker is the approved
existing encoder snapshot (including matching auxiliary configuration), its frozen
CPU runtime, and independently anchored safe index/key metadata. Provisioning or
moving those assets requires the owner's selected approved source; this probe does
not download weights or install packages automatically. Preserve the frozen score,
margin and sibling gates listed in [KNOWN-SPEC-SERVICE-v1.md](KNOWN-SPEC-SERVICE-v1.md).

Focused tests verify exact-path inspection, whitelisted override/default handling,
no array/model loading, and mismatched synthetic bytes never being marked verified:

```sh
python3 -m unittest projects.algorithm_solver.catalogue.test_recognition_assets
```

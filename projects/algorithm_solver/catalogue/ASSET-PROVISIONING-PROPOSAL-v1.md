# Goal1b: bounded CPU asset-provisioning proposal

**Proposal only: no weights/wheels downloaded, packages installed, encoder
instantiated, training performed or calibration changed.** The native-dot probe
reported the five checked model-side paths and four index paths absent; the native
Python3.13 environment has NumPy2.2.4 but lacks the other encoder packages.

## Smallest concrete owner approval

Authorize downloading only the six listed encoder files from the immutable
official revision below into a private workspace model directory, verifying every
hash, and preparing an isolated workspace-only Python3.13 CPU virtual environment
with the exact dependency lock. No system package changes, GPU/CUDA/ROCm packages,
paid services, protected data, full-corpus loaders, training or deployment. Source
statements/index materialization and recognition evaluation remain separate gates.
An explicit disk ceiling is a permission bound, not an assertion about installed
size; stop rather than expanding the approved resource envelope.

## Exact historical encoder identity recovered

Official repository **Qwen/Qwen3-Embedding-0.6B**, immutable revision
`97b0c614be4d77ee51c0cef4e5f07c00f9eb65b3`, matches BOTH SHA256 values in Gamma's
pinned historical `embed.py`. This is not a guessed successor model. The
[immutable official tree](https://huggingface.co/Qwen/Qwen3-Embedding-0.6B/tree/97b0c614be4d77ee51c0cef4e5f07c00f9eb65b3)
and its [metadata API](https://huggingface.co/api/models/Qwen/Qwen3-Embedding-0.6B/tree/97b0c614be4d77ee51c0cef4e5f07c00f9eb65b3)
bind Git blob identities, exact sizes and the two LFS SHA256 values.

| File | Exact bytes | SHA256 |
| --- | ---: | --- |
| model.safetensors | 1,191,586,416 | `0437e45c94563b09e13cb7a64478fc406947a93cb34a7e05870fc8dcd48e23fd` |
| tokenizer.json | 11,423,705 | `def76fb086971c7867b829c23a26261e38d9d74e02139253b38aeb9df8b4b50a` |
| config.json | 727 | `b5bf1f51fc45be473a54718cef92448d90a1be001bf9b9a44b8c7f10a19feaa9` |
| tokenizer_config.json | 9,706 | `253153d0738ceb4c668d2eff957714dd2bea0b56de772a9fdccd96cbf517e6a0` |
| generation_config.json | 117 | `28396d421a2108acce96383f6a7de78008f7f1b17f807958f3c14c51dbfb65fb` |
| README.md (license notice/model card) | 17,237 | `c34d9b7e5a267ad3fdd13227a253686bc90844ff4744a2a6a86c7c905e3d06f3` |

Total encoder bytes: **1,203,037,908** (1.203GB decimal, about1.120GiB), both
network payload and single-copy file storage excluding filesystem/cache overhead.
The two large-file identities/sizes were read from official LFS metadata, not the
weight/tokenizer payload. Small raw configuration/model-card bytes were read to
compute SHA256 and independently matched against Git blob SHA1/size in the tree.
The [model card](https://huggingface.co/Qwen/Qwen3-Embedding-0.6B/blob/97b0c614be4d77ee51c0cef4e5f07c00f9eb65b3/README.md)
declares Apache-2.0; preserve that attribution/license notice. The repository
has no standalone LICENSE and **no special_tokens_map.json** at this revision:
pin the absence rather than inventing or obtaining one from a different snapshot.
`generation_config.json` is the third available auxiliary configuration; it is
not an excuse to enable generation. No sentence-transformers or alternate model
files are needed for Gamma's direct AutoModel route.

## Runtime identity is a separate unresolved historical binding

The immutable Gamma run contract records torch2.12.1+ROCm7.2 and
transformers5.13.1 for its **generative** backend. The inspected
[qualification_environment.py](https://github.com/clocksmith/gamma/blob/32b0e46bc2909cde11659bc2927737791a4a28a1/projects/algorithm_solver/algsolve/qualification_environment.py)
binds judge executables/stdlib, not encoder dependencies. Therefore neither proves
an exact historical CPU encoder environment. The model config's transformers4.51.3
is model-export metadata, also not a serving-runtime lock. Do not silently select
that older version: Gamma's pinned encoder passes `dtype=` to `from_pretrained`.

A proposed CPU environment can retain nominal torch2.12.1/transformers5.13.1
versions, but its new CPU build and dependency closure must be frozen and checked
as a distinct runtime. It is **not** automatically covered by old recognition
calibration or historical release results. Preserve all existing thresholds and
sibling gates; demonstrate matched encoder/index behavior under a separately
recorded allowed verification before claiming reuse. No automatic recalibration
or qualification is authorized by provisioning.

## CPU dependency proposal and storage accounting

Target is normal (GIL-enabled) **CPython3.13 Linuxx86_64**; native architecture was
confirmed by the parent. Verify glibc>=2.28 before installing the selected official
torch wheel. Use a fresh workspace venv, not the system Python's packages.

- `torch==2.12.1+cpu`: official CPU-index wheel
  `torch-2.12.1+cpu-cp313-cp313-manylinux_2_28_x86_64.whl`, **192,272,034bytes**,
  SHA256 `77d049968c7817456dbdebf0aadcac0813e302218b0e857a8723463331339d55`.
  Its PEP658 metadata hash was checked against the index:
  `2dd7308d91027a8d24fe97f0982dca9a304814248869fb289c1d54e8e6c388ff`.
  Metadata requires Python>=3.10 and **no CUDA/ROCm dependencies**.
  [Official CPU index](https://download.pytorch.org/whl/cpu/torch/) and
  [official previous-version installation guidance](https://pytorch.org/get-started/previous-versions/).
- `transformers==5.13.1`: universal wheel **11,503,977bytes**, SHA256
  `53f0ea8aa397e29244c2377ba981bcaf0c87adcf44fbdd447ef6306522afcacd`;
  Python>=3.10, Apache2.0.
  [Official publisher package metadata](https://pypi.org/pypi/transformers/5.13.1/json).
- `tokenizers==0.22.1`, `safetensors==0.8.0`, `numpy==2.2.4`: fixed
  Python3.13-compatible wheel tags and declared Python version ranges; matched to
  Transformers5.13.1's declared constraints. Their exact binaries/hashes and full
  transitive closure are recorded in the companion CPU proposal. This is
  **metadata compatibility, not a successful import/inference test**.

Do not use plain PyPI `torch==2.12.1` on Linux: its published dependency metadata
includes GPU packages. Restrict torch to the explicitly hashed CPU artifact.
No sentence-transformers, torchvision, torchaudio, accelerator stack or compiler
build is necessary for this route. Freeze all remaining transitive wheels and
hashes before installation, use wheels only, and do not permit the installer to
silently select new versions or source builds.

Unpacked-wheel footprint, interpreter venv overhead, bytecode and filesystem
allocation are not available from the PyPI file-size metadata alone. Report the
compressed download total separately from any planning allowance. A conservative
workspace **4GiB hard ceiling** can bound the six model files, venv, retained
wheels and staging, but is an authorization/resource cap, **not a measured unpacked
size or guarantee**. Stop before exceeding it. Avoid duplicate model caches; use
one private model directory and offline/local-only reads after provisioning.

## What this approval does not settle

Exact model bytes are now identified, not missing provenance. The remaining
unsettled identity is the historical CPU runtime/index combination. Safe
source-free candidate metadata and the existing exclusion closure, pinned index
vectors/key order, query public verification, language-specific serving and frozen
recognition precision/coverage/latency gates remain required. The old unsafe
full-corpus loader remains prohibited. No successful1b claim, protected scoring,
source-publication permission or threshold relaxation follows from asset approval.

## Final metadata-only lock and bounded request

The [encoder manifest](ENCODER-PROVISIONING-PROPOSAL-v1.json) records all six
immutable file URLs, sizes, SHA256 values and Git blob identities. The
[CPU environment manifest](CPU-ENVIRONMENT-PROPOSAL-v1.json) records **34 wheels**
including torch, every exact version/URL/size/SHA256, active dependency constraints,
Python requirements and publisher license metadata. Its dependency closure was
checked against normal CPython3.13 Linuxx86_64 markers, all selected version
constraints and release dates; no runtime code from those packages was executed.
The wheel hashes are publisher metadata pins, to be verified against actual bytes
only after approval. PyTorch's CPU wheel size was obtained with HTTP HEAD, and its
small PEP658 metadata was checked against the official index hash.

- Encoder payload: **1,203,037,908bytes**.
- Complete compressed CPU-wheel payload: **243,632,896bytes**.
- Combined payload: **1,446,670,804bytes**, about**1.447GB /1.347GiB**.
- Existing NumPy is deliberately not reused through system-site-packages; the
  isolated environment includes its own pinned NumPy2.2.4 wheel.
- A **rough planning allowance**, not a measured extraction result, is up to
  four times the compressed wheel bytes (974,531,584bytes) for unpacked packages.
  Combined with one extra encoder-sized staging copy, model files and retained
  wheels, that totals3,624,240,296bytes (about3.375GiB), before remaining overhead.
  The proposed **4GiB hard workspace ceiling** is therefore a bounded planning
  envelope, not a mathematically proven unpacked-size upper bound. Check actual
  usage and stop rather than exceeding it or silently adding caches.

Suggested approval scope: **download these six encoder files and34 pinned CPU
wheels (about1.45GB total), verify their hashes, and install only into a fresh
workspace Python3.13 venv under a4GiB disk ceiling.** Do not activate model
inference/training, alter calibration, read protected data, install system/GPU
packages or deploy a service as part of that permission. Subsequent safe-context
and matched-verification work must retain its own explicit run contract.

Package artifacts are supplied by the official PyTorch CPU index and each
publisher's PyPI release metadata, not third-party wheels. Retain all wheel
license/NOTICE files, including bundled third-party notices; top-level Apache/BSD
labels do not replace those notices. This proposal is reproducibility/provenance
metadata, not an audit of package security or a legal license opinion.

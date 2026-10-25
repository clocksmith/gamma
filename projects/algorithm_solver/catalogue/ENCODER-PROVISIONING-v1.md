# Approved encoder provisioning: completed native diagnostic

The exact approved [encoder](ENCODER-PROVISIONING-PROPOSAL-v1.json) and
[CPU environment](CPU-ENVIRONMENT-PROPOSAL-v1.json) were provisioned into a private
workspace directory. [Receipt](ENCODER-PROVISIONING-RECEIPT-v1.json) records:

- 40 artifacts, all exact sizes/SHA256 checked: **1,446,670,804bytes**.
- 34 wheels, **889,566,301bytes** of ZIP-declared uncompressed members and68
  license/NOTICE members, inspected before installation.
- Offline, hash-required, wheel-only installation into a fresh Python3.13 venv;
  no system installation, dependency resolution/network fallback or bytecode
  compilation. Existing pip26.2.2 was invoked with native Python and its
  `__main__.py` identity recorded; no installer package was added.
- Native `/usr/bin/python3`3.13.5, x86_64, glibc2.41; `pip check` reported no broken
  requirements. All34 installed versions exactly matched the manifest.
- Workspace after smoke: **2,383,089,664bytes**, below the **4GiB** ceiling.
  This includes retained wheels and model files; nothing was silently cached in
  another model directory or published with the repository.

## Code and operation

`provision_encoder.py` has explicit `download`, `inspect` and `install` stages.
Both input manifests require independent SHA256 arguments. It accepts only the
listed official origins, verifies each exact artifact, checks free space and the
workspace ceiling throughout, retains partial failures, and supports only bounded
HTTP Range resumption. Existing exact artifacts are reused without network access.
Before native installation, it rechecks all hashes and reserves twice the measured
ZIP uncompressed bytes plus128MiB in addition to existing workspace use. It also
monitors disk usage during installation and stops on budget failure. Lifecycle,
checksums, wheel-notice inventory, installation output and native exit status are
retained privately. Cleanup, if needed, is limited to this owned staging directory.

Example invocation (operator supplies exact approved paths/digests):

```sh
python3 -m projects.algorithm_solver.catalogue.provision_encoder \
  --encoder /approved/encoder.json --encoder-sha256 "$ENCODER_MANIFEST_SHA256" \
  --cpu /approved/cpu.json --cpu-sha256 "$CPU_MANIFEST_SHA256" \
  --root /workspace/shared/approved-encoder-runtime --stage download
```

Repeat with `--stage install` **only in the approved native dot Python namespace**.
Installation refuses the wrong Python version, architecture or executable. It uses
an existing trusted pip tool, never an ELF-loader/noexec workaround or an unpinned
bootstrap download. The private venv is not a new production service.

## Diagnostic result and limits

`encoder_smoke.py` checks the exact model and installed package identities, forces
local/offline loading with `trust_remote_code=False`, runs CPU float32, and embeds
six independently authored short texts. No source, cases, protected problem
metadata, legacy corpus loader or existing index is consumed. It records finite
1024-dimensional normalized vectors and diagnostic nearest-document indices, not
an accepted algorithm/problem answer.

The first completed native diagnostic used **4 threads**, matching the inspected
historical encoder setting. It completed in12.855seconds after initial artifact
checks, including11.252seconds for imports/model loading. All six authored texts
had their corresponding document as the nearest vector; repeat-vs-batch maximum
absolute difference was approximately1.60e-7. These timings are one diagnostic,
not cold/warm p50/p95 or full-path serving performance. Memory peak was not
measured. No old threshold/calibration was used or changed.

A resource-coordination request arrived after the native job launched. That
already-completed4-thread receipt is preserved honestly, with the exact original
smoke source archived and hash-bound. **Future smoke defaults to2 threads and only
accepts1 or2**; do not retrospectively label the initial result a2-thread run.
Do not launch further model work during another owner's reserved CPU operation.

The model-loading/CPU-runtime blocker is now resolved for this exact private
installation. Historical CPU-runtime equivalence, safe source-free index
construction and exclusion closure, existing precision/coverage gates, query
public verification, separately qualified language implementation selection and
end-to-end serving latency remain separate. This is **not goal1b qualification**,
full catalogue coverage, protected scoring, training, deployment or automatic
reuse of prior calibration. Original compact-library M1 remains unmet.

Focused development checks: four synthetic provisioning tests plus compilation
of the provisioner, diagnostic and tests. Synthetic tests cover immutable artifact
reuse without network, manifest/disk failure, wheel size/license inspection without
execution and unsafe archive paths. The actual native install, `pip check` and
encoder diagnostic are separately recorded evidence, not substituted for these
unit tests or for recognition acceptance.

## Reusable encoder-only adapter

`cpu_encoder.PinnedCPUEncoder` provides the bounded offline encoder independently
of all corpus/index/answer modules. Its constructor requires the approved encoder
and CPU manifests **and their external SHA256 anchors**, the model root and the
native Python executable hash. It is lazy: construction/identity inspection does
not import torch/Transformers or read model weights. On first nonempty encode it
checks all six model-file hashes, native Python identity and all34 installed
package versions against the verified-wheel manifest before importing the runtime.
This version check is **not** a fresh installed-file byte audit; the installation
receipt retains the exact wheel hashes and installation provenance separately.

```python
encoder = PinnedCPUEncoder(
    approved_model_root,
    encoder_manifest=approved_encoder_manifest,
    encoder_manifest_sha256=approved_encoder_manifest_sha256,
    cpu_manifest=approved_cpu_manifest,
    cpu_manifest_sha256=approved_cpu_manifest_sha256,
    native_python_sha256=approved_native_python_sha256,
    threads=2, batch_size=2,
)
# Only when the public text population and compute run are authorized:
# vectors = encoder.encode(public_texts, query=True)
```

It enforces CPU float32;1–2threads; batch size1–4; at most64texts per call and
16,384characters per text; left padding;1024-token truncation; the pinned query
instruction only for queries; last-token pooling and L2 normalization. Empty
batches return an empty1024-wide array without loading the model. Both AutoTokenizer
and AutoModel require `local_files_only=True` and `trust_remote_code=False`, with
offline hub settings and cache paths inside the private runtime directory.
Unexpected dimensions/nonfinite results fail closed. It neither chooses problem
identity nor owns confidence, thresholds, approval, protected-boundary decisions
or source selection. It does not create/load an index.

Six additional source-only unit tests check resource/input limits before loading,
query/document preparation, laziness, actual running-interpreter identity, explicit
truncation metadata and non-recognition identity. No additional encoder run was
made while native UI/resources were reserved. After explicit clearance, the
separate2-thread adapter diagnostic below was run; the earlier4-thread receipt
remains historical and unchanged.


## Two-thread adapter: separate native verification

The [successor native receipt](CPU-ENCODER-NATIVE-RECEIPT-v1.json) binds the exact
adapter and smoke source hashes, approved manifest hashes and actual resolved
running-interpreter hash. It records CPUfloat32, **2torch threads /1interop thread**,
private-venv identity and six authored-text diagnostics. Initializing a conflicting
interop pool fails rather than silently ignoring the mismatch. The adapter records
pretruncation token counts, modeled counts and truncation flags for each call;
these are semantic-loss warnings, not proof that a full specification is preserved.

The native process completed with exit0, visually confirmed at the owned terminal,
under180seconds wall limit,120/125CPU-second soft/hard limits and8GiB virtual-memory
limit. Actual total was12.055seconds; Linux peak RSS was3,946,328KiB. After-run
workspace use was2,383,130,624bytes under the separate4GiB disk ceiling. All six
queries yielded1024-dimensional finite unit vectors, no input was truncated, and
the corresponding authored document was nearest for each query. No score/margin
threshold or prior calibration was reused. These are diagnostic outcomes only,
not informal-recognition precision/coverage or full-path performance evidence.

Both original4-thread and successor2-thread source snapshots are hash-bound and
read-only in the private evidence directory. No raw embedding vectors, model
weights, signed download URLs or user home paths are included in public receipts.
The separate original receipt retains all40 verified artifact hashes and all34
installed package versions. No additional downloads, candidate/case/protected
reads, training, full-corpus index loads or deployment occurred during the adapter
verification. Provisioning and this adapter checkpoint are complete; safe-context
and recognition release gates remain open.

Timing caveat: the two-thread receipt's first-document batch includes lazy
initialization; the total also includes subsequent query/repeat work. OS file
cache state was not controlled, so neither number is a cold-OS-cache benchmark.
The approximately3.76GiB measured peak resident memory is a RAM observation,
not the approved4GiB disk cap. Future full-path1c measurements must include
initialization versus warm requests, recognition, query verification and serving,
with explicit process memory/time budgets and no overlapping heavy judge/build.

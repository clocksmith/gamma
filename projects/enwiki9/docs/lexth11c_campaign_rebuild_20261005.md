# Lexth11c rebuild, measured adaptations and isolated GPU control

The pinned donor builds offline with LLVM/Clang 17.0.6, GCC 12.2 headers and
shared runtime, and UPX 5.1.1. The original tagged source, model, preprocessing,
PPMD heap and kernels remain unchanged. The finite donor control passes;
complete full-corpus reproduction is still running. No qualified package or
verified full-1G score is claimed.

## Produced files and controlled deltas

| Measurement | Result | Evidence |
| --- | ---: | --- |
| Released downloaded compressor plus archive plus 12 option bytes | 99,313,762 bytes | [Original accounting](../operations/provenance/lexth11c_accounting_20261004.json) |
| Corrected offline rebuilt compressor | 3,477,188 bytes; 51 more than release | [Rebuild control](../results/lexth11c_rebuild_control_q0_v3/result.json) |
| Corrected rebuilt executable stub | 198,288 bytes; 52 more than release | [Full replay plan](../operations/planning/lexth11c_full_recompression_v4_20261005.json) |
| Lossless repacking against the preserved first-toolchain parent | 509 more bytes per weight copy; 3,696 added implementation bytes; net saving **−4,714 bytes** | [Retired comparison](../results/lexth11c_lossless_repack_q0_v1/result.json) |
| Separate diagnostic CLI specialization | 197,348-byte stub; 940 saved per copy; **1,880 counted component bytes saved** | [Specialization comparison](../results/lexth11c_executable_specialize_q0_v1/result.json) |

The corrected donor, released binary and deterministic repeat produce identical
6,287-byte raw control archives and identical 20,522,960-byte native prediction
streams on the complete causal 50,051-byte tagged fixture. Independent inverse
matches the original fixture. These controls do not reproduce the billion-byte
score. The corrected order file is one byte smaller than release; the complete
native replay must resolve that difference using actual output files.

The first toolchain generation silently selected static libstdc++ because its
shared-library symlink target was absent. Its source and failed/finite control
receipts remain preserved. A separate immutable toolchain generation adds the
exact GCC 12 shared runtime. This build correction earns no saving against the
released donor by itself.

The repacking comparison preserves all 435 raw typed and native-promoted tensors
bit for bit, including floating-point tensors. It excludes Zmix's lossy
`ENC_BF16_F32` conversion. Parent, treatment and repeat prediction streams and
archives match, and inverse is exact. Its one declared continuous-count
configuration, measured against its matched first-toolchain parent, is retired
after the negative paid result. This does not reject
all class-conditioned representations or compressed-size training objectives.

Specialization changes only `runner.cpp` diagnostic long-option dispatch and
Help. Its packed model, dictionary and order remain byte-identical to the
corrected donor; native streams, archive, repeat and inverse controls pass.
Both actual executable copies are counted. Full payload preservation is still
unverified, so the 1,880-byte gain receives no full-corpus objective credit.
The conditional arithmetic, if full payload remains unchanged, is 99,311,985
complete bytes, leaving 1,311,985 bytes to 98M. It is a forecast, not a score.

## Training runtime and new schedule

The separate Python 3.12 environment imports PyTorch 2.9.1 with ROCm 7.2.1 and
Transformers, and executes on native `gfx1151` without the architecture override.
Dependency versions, wheel/deb hashes and loaded userspace libraries are retained
in the [environment receipt](../operations/provenance/lexth11c_gpu_environment_20261005.json)
and [operation receipt](../results/lexth11c_gpu_export_control_q0_v1/operations.json).
Existing host dependencies and drivers are unchanged.

The dequantized FP16 reference executed but differed from native logits by
1.562758207321167. A separate integer-domain control preserves W4/W8/A8 dot
products and original FP32 row-then-token scaling. On eight synthetic tokens,
its maximum native logit difference is 2.86102294921875e-6 and probability
difference is 4.172325134277344e-7. All 119 linear sites execute; 208 gradient
tensors are finite and a fresh AdamW step changes parameters. The backward is
an explicitly approximate reference Jacobian; native forward values enter loss.
The probe discards its updated model.

Before any update, all 435 original typed tensors survive actual import/export
bit for bit. An independent native pass over the exported raw file is
bit-identical to the released packed-model native pass.
[Export result](../results/lexth11c_gpu_export_control_q0_v1/result.json).
These are runtime and unchanged-model controls, not full-training readiness.
Ubuntu 26.04 is outside [AMD's published native Linux OS matrix](https://rocm.docs.amd.com/projects/radeon-ryzen/en/latest/docs/compatibility/compatibilityryz/native_linux/native_linux_compatibility.html),
whose framework validation is FP16. Successful local execution remains diagnostic evidence.

The [separate resumed-training proposal](../operations/planning/lexth11c_resumed_training_contract_20261005.json)
initializes released weights with fresh optimizer state, defines a new schedule,
matches data and updates across ordinary QAT and size-penalized QAT, and specifies
the penalty formula. It does not reproduce run11 or Zmix. Their unresolved
historical recipes and Gamma's closed 512-target contracts remain unchanged.
Actual causal full-data prior capture/alignment, measured compressed storage,
updated-checkpoint native validation and an admitted frozen trainer remain
prerequisites. Dense priors still project to 241–301 GB; no storage reduction
has been measured and sharding alone receives no capacity credit.

## Live reproduction and remaining certificates

The original released full decode remains on CPU 2 under its existing owner and
guard. The corrected rebuilt full replay has a separate owner, CPU 12, 12 GiB
aggregate memory cap, 32 GB scratch cap and 360,600-second aggregate stop. It
first checks the restricted pinned runtime against retained control artifacts,
then runs full encode, fresh-directory repeat and no-argument inverse without
canonical input or source access. Its
[frozen experiment](../operations/adaptive/experiments/lexth11c_recompress_full1g_q0_v4.json)
counts produced files with `S=A+2W+C`, including 12 option bytes.

Three pre-payload failures remain recorded: the original corpus symlink was rejected
before codec execution, then an initial guard sample observed `taskset` before
its affinity narrowed. The restricted-runtime canary then passed, but full phda9 preprocessing required
`tmpfile()` in a missing `/tmp` and exited 139 before producing payload. The
repaired replay uses a hash-verified regular corpus asset, pins the admission
controller before any child is spawned, and mounts private `/tmp` charged to
the aggregate memory cgroup. These failures are execution-boundary defects;
the donor predictor and existing released decode remain preserved.

Retain the 96,000,000-byte objective and 98,000,000-byte intermediate target.
The diagnostic encode has an observed aggregate cgroup peak above 10 billion
bytes; its native process RSS and aggregate usage are different measurements.
Qualification must replay under its own decimal limit and complete certificate.
Full score, specialized full replay, Intel/AMD agreement, independent repeated
reconstruction, isolated single-core calibration, and measured memory within
10,000,000,000 bytes remain open. A 12 GiB diagnostic envelope is not that memory
certificate. Recheck prize submission order and predecessor before filing.

Continue through `python3 tools/enwiki9_lab.py start` and the identity-bound job
records. After each terminal replay, validate its reflection before selecting a
descendant. Preserve exact produced archives, hashes, accounting and failures.

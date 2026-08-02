# Endpoint428 CPU and thread eligibility contract

Candidate: `endpoint428_gate_dot_fuse_output_update_loop_v1`

Status: frozen zero-credit preflight; no timing or eligibility verdict

## Purpose

Before any clean runtime replay, mechanically determine whether the exact
endpoint428 process and thread topology is permitted by the authoritative
Hutter Prize rules. Existing receipts bind archive, package, roundtrip, and
memory facts, but they do not bind runnable threads, affinity, OpenMP state,
host calibration, or the rule interpretation needed for an eligibility claim.

This contract can emit one scientific decision:

```text
REJECT
AUTHORIZE_CLEAN_10M_RUNTIME_SCREEN
```

Missing or malformed evidence emits `MALFORMED_EVIDENCE` with nonzero process
status and no scientific verdict. No disposition changes archive score,
forecast credit, or full-1G status.

## Frozen source identity

The preflight must reconstruct the counted minified source package and verify
these exact identities before inspecting topology:

| Artifact | SHA-256 |
|---|---|
| Minified source package | `b6fe6b09d6adbd8a287a08d284ca1f439ba72ff007b4d40c66bf7647a54a5d43` |
| Backend | `d1066630f0d58894e69bd84519ec7d0f608b9e2fce67ab9ebedde65c58eca194` |
| Wrapper | `37ee8cd73ade9845b1afcb39f3bbd9358956c3ff9aea3b69328da7441ee32361` |
| Makefile | `9ab300f6b369e5ca1f067fb07a0abe08d95bc2a3332b3fefb791b201a2520d8b` |
| `src/mixer/lstm-layer.cpp` | `7b9d4fed31a1a6108046e158c27fbb7e9ea18f377b1e7534c98081d1881da489` |
| `src/mixer/lstm.cpp` | `0a5739a001fd651ec5a26a7f0e61e79e1e401e84bcc00c4e0b8fa4e69e87f10e` |
| `src/fx2lite/endpoint428.cpp` | `e9c7f7c3ac7c2ec2c220167b679a6752c3f43c632d7d0c523196cc46eed5f40b` |
| `src/predictor.cpp` | `016611062493552e90f4fa22c7b6d037ef3dbdf9ac76ad882f9c2f2b193e8e4d` |
| `wrapper.c` source | `ce2722c05032991b0102a03b8bcb60b4af2d8b8c81ac18c59260b31c76c89b81` |

The original and minified source trees must be code-identical after the frozen
comment-removal transformation. A different source topology is a new child,
not endpoint428 eligibility evidence.

## Static concurrency inventory

The exact source contains all of the following:

- OpenMP compilation and static `libgomp` linkage through `-fopenmp` and
  `-lgomp`.
- Hard-coded `num_threads(3)` regions in `LstmLayer::ForwardPass`,
  `LstmLayer::BackwardPass`, `Lstm::Perceive`, and `Lstm::Predict`.
- A persistent `std::thread` running `Endpoint::RunWorker`.
- `Predictor::Perceive` releases that FX2 worker before compact-CMIX update so
  the paths can overlap.
- The wrapper forks the codec child and waits in the parent.

Static inspection therefore permits a three-thread OpenMP team to overlap the
FX2 worker, while the wrapper parent normally waits. This is an inventory, not
a legality conclusion. Observed live and runnable maxima must be measured.

## Authoritative rule binding

The preflight receipt must store, rather than infer:

```text
rule authority URL
retrieval UTC timestamp
content SHA-256 or immutable snapshot
quoted section locator
adopted processor/core/thread interpretation
reviewer or verification method
```

The adopted interpretation must explicitly decide whether the source topology
above is permitted. Missing, ambiguous, or internally inconsistent rule
evidence yields `MALFORMED_EVIDENCE`; it cannot be replaced by a benchmark
convention or an assumption about idle threads.

## Required observed topology

For both compression and decompression, record:

```text
exact command and environment
wrapper PID and codec child PID
descendant process tree over time
allowed CPU affinity for every process
physical cores and logical CPUs in that affinity
OpenMP runtime and linked-library identity
OMP_NUM_THREADS, OMP_DYNAMIC, OMP_NESTED, OMP_PROC_BIND, OMP_PLACES
maximum live threads per process and process tree
maximum simultaneously runnable threads per process and process tree
per-thread CPU time and total process-tree CPU time
CPU model, topology, governor, and frequency policy
GPU and network absence
competing-process audit
```

Sampling must cover startup, preprocessing, steady compression or
decompression, recurrent retraining, flush, and teardown. Enumerating only
process RSS is insufficient; the collector must sample `/proc/<pid>/task`,
thread state, affinity, and CPU counters for every descendant.

## Reference calibration and clean 10M screen

The later timing receipt must bind the exact Geekbench5 version, command,
result, and host score `T`. It then runs independent compression and
decompression on the exact canonical 10M archive identity:

```text
archive bytes   1,634,500
archive SHA-256 93d7f5cb69ecad5457078ff9de34a63d8b0a8dcf21cc0fa9e20df895e13b1880
```

Each direction independently must satisfy:

```text
elapsed_10m_seconds < 2,520,000 / T
```

The receipt also binds exact raw roundtrip, deterministic re-encode, decimal
10GB process-tree RSS, temporary disk, counted package, no GPU, no network, and
clean-host evidence. Passing 10M authorizes only one full-1G resource proof.

## Mechanical decision

Return `MALFORMED_EVIDENCE` with nonzero process status when any source hash or
required receipt field is absent or inconsistent. Return `REJECT` with process
status zero only when complete evidence establishes that the frozen source
topology violates the adopted authoritative concurrency condition. A valid
rejection must not trigger a thread-count, affinity, compiler, or environment
rescue sweep under the endpoint428 identity.

Return `AUTHORIZE_CLEAN_10M_RUNTIME_SCREEN` only when the exact topology is
fully observed and explicitly permitted by the frozen authoritative rule
interpretation. Do not run that screen while another heavy gate owns the lock
or while endpoint428 remains above the score target without a target-bearing
child.

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

A 2026-08-02 read-only audit initially identified an apparent wording boundary:
the prize homepage and FAQ use single-core language, while the detailed timing
page presents both one-core and multicore reference calibration values. The
current official pages resolve the broad interpretation. The homepage requires
execution using a single CPU core, and the FAQ explains that a `C`-core
algorithm does not receive a `100/C` wall-clock allowance. The multicore
Geekbench values in the detailed rules describe available test machines; they
do not authorize multicore execution. Use the one-core Geekbench score for the
time inequality.

The exact retrieved page identities are:

| Page | Retrieved UTC | Bytes | SHA-256 | Last-Modified |
|---|---|---:|---|---|
| `https://www.hutter1.net/prize/` | `2026-08-02T19:59:48Z` | `48,606` | `065186dc3e6ef61f295aa30873c142bd6e4a2f6f310cfbd1d28ec09cbc6cbff7` | `2025-05-30T14:08:29Z` |
| `https://www.hutter1.net/prize/hrules.htm` | `2026-08-02T19:59:49Z` | `15,907` | `e55d9f96b227e61ec0996adaf36304185d74db8c17093b403bb325240b2dc163` | `2024-10-09T19:15:29Z` |
| `https://www.hutter1.net/prize/hfaq.htm` | `2026-08-02T19:59:50Z` | `96,252` | `9233864b9ab2ce7b75ca2092416b518b196fcd498ab4e70e8c8f20b1bc42f52b` | `2025-05-30T14:08:29Z` |

The controlling locators are homepage `The Task` restriction, detailed-rules
`Rules` resource paragraph, and FAQ `Why do you restrict to a single CPU core
and exclude GPUs?`. The verification method is literal cross-page consistency:
the specific single-core statements control the test-machine inventory.

One narrower policy question remains unresolved without committee confirmation:
whether several software threads time-sharing one allowed logical CPU count as
single-core execution. Therefore the current unconfined endpoint428 topology
must not be called eligible, and the affinity preflight below may establish
observed one-logical-CPU use but cannot by itself establish final prize
eligibility. The live authoritative pages are:

```text
https://www.hutter1.net/prize/
https://www.hutter1.net/prize/hrules.htm
https://www.hutter1.net/prize/hfaq.htm
```

## Bounded external-policy preflight

One source- and archive-neutral topology check remains unmeasured: run the
exact binary under verifier-imposed single-logical-CPU affinity, optionally
with `OMP_THREAD_LIMIT=1`, and collect the full observed topology required
below. `OMP_NUM_THREADS=1` alone is insufficient because the source contains
hard-coded `num_threads(3)` clauses.

This preflight can answer only whether the exact archive remains unchanged and
whether every runnable thread is confined to one logical CPU. Committee
confirmation or an explicitly adopted submission-time interpretation is still
required to decide whether multiple time-sharing software threads satisfy the
single-core rule. If the entrant must supply affinity or environment text,
count every required command-line byte under the rule snapshot. Do not assume
that verifier-imposed policy is a free archive dependency.

The preflight is not a runtime rescue and is not authorized while the score
target is missed or another heavy job holds the lock. Existing active/passive,
worker-count, spin-count, serial, persistent, and BPTT evidence leaves only
`13.963%` optimistic exact-source leverage against the repository's prior
`83.093%` runtime-reduction screen. The exact 10M timing receipt is contaminated
by competing CPU work, so there is no clean official runtime rejection; the
planning conclusion is nevertheless model-work removal or replacement, not an
environment sweep.

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

# First prefill channel-gain experiment

**Continuation 02 is active, 2026-11-13.** The owner rejected the budget-only stop
because it left the shader question unanswered. The [continuation policy](protocol-continuation-02.json)
keeps the original 1% setup-efficiency target as a scored criterion, but allows the
fixed eight selection and 176 confirmation requests to finish. Candidates, tasks,
controls, k=2 and hidden-test separation are unchanged. [Stage lock 04](native-stage-lock-04.json)
pins this policy and runner before selection. The earlier closed run below remains
preserved; it is not the current execution status. See [execution-status.json](execution-status.json).


**Run closed at selection admission, 2026-11-13. No shader-improvement confirmation.**
The complete two-task smoke and corrected public replay ran. The eight-request
selection workload was not admitted under the unchanged 35.59 GPU-second cap;
both candidates remain **untested**, with no winner and no confirmation requests.
This outcome applies to this implementation and budget, not every gain rule or
reconfiguration architecture.

The current state is [execution-status.json](execution-status.json). Detailed
request, cost, cache, reset and memory tables are in [RESULTS-03.md](RESULTS-03.md)
and [results-03.json](results-03.json). The [selection receipt](native-selection-03/selection-receipt.json)
is the decision source of truth.

## What ran and what it showed

Qwen3.5-9B used the provisioned revision and an explicit native split-F32 MLP path
on Jupiter's AMD GPU. The rule was fixed at beta +0.05 for smoke, layers 30/31,
clip 1, epsilon 1e-6 and reference A. No offline training or additional transform
family was introduced. Smoke did not rank the positive/negative candidates.

There were 22 generated smoke responses: two base, sixteen actual/shuffled/random/
permuted-gain responses across two cache arms, two seed-47 adapter responses, and
two extra base samples. Public-only best-of-2 selected among the existing samples.
All four gain types reused identical hashes between their cache arms on both tasks.
All-projections is **not applicable**, neither passed nor failed.

| Condition | Public tasks passed | Mean attributed request time |
| --- | ---: | ---: |
| Same-prompt base | 0/2 | 93.17 s |
| Actual gain, base cache | 0/2 | 101.61 s |
| Actual gain, re-prefill | 0/2 | 114.84 s |
| Shuffled gains, base cache / re-prefill | 0/2 / 0/2 | 113.12 / 126.12 s |
| Random gains, base cache / re-prefill | 0/2 / 0/2 | 102.03 / 114.69 s |
| Permuted gains, base cache / re-prefill | 0/2 / 0/2 | 102.25 / 115.39 s |
| Trained seed-47 adapter | 1/2 | 94.60 s |
| Public-selected best-of-2 base | 0/2 | 192.96 s for both samples |

The base and gain outputs failed the required workgroup-override source contract.
The repaired verifier accepted the adapter's sign-bit shader. Its tent shader
compiled/dispatched but failed the public numeric oracle (one of four elements).
These are two smoke families, not a held-out quality estimate. Prompt-dependence,
trained-adapter gap closure and wrong-acceptance criteria remain unevaluated on
confirmation. The full best-of-2 base samples consumed 1.77x and 2.04x the primary gain
request's attributed compute; base-favoring integer rounding is reported, not exact
compute equality.

Mean paired added latency was 9.13% for base cache and 23.33% for re-prefill. Output
lengths differed: base averaged 278.5 tokens and actual gains 270.0. These descriptive
smoke observations do not pass or fail the confirmation latency criterion. Timing
includes token preparation, reference/base prefill, gain derivation, snapshot
restoration or re-prefill, decode, request cleanup and public verification. Shared
setup is charged back to each arm; physical batch wall time is reported separately.

## Cache, reset and memory

Both same-prefix cache diagnostics measured nonzero differences at layer 31 only;
earlier KV layers and all 24 recurrent states matched. Output-logit relative L2
was 0.00173923 and 0.00219784, with unchanged top-1. After discarding gains, fresh
base prefill reproduced all 248,320 original logits bit-for-bit on both prompts.
This supports sequential reset and this cache comparison; it does not establish
concurrent request isolation, cross-domain switching or full-model weight-byte
invariance. Private gain ownership and unchanged toy weights have separate native
operator tests.

Each frozen gain had 98,304 logical bytes and 131,072 allocated GPU bytes. The
base-cache arm's measured retained increment was 131,072 bytes. Re-prefill retained
326,201,344 bytes including the original snapshot kept by this interleaved harness;
that exceeds the 232,821,904-byte adapter reference. This is the current harness's
storage cost, not proof that re-prefill inherently requires an extra saved cache.
The complete model-device process peak was 23,476,542,680 bytes. It is a process-wide
GPUBuffer high-water mark, not per-request physical VRAM. Preparation scratch,
baseline subtraction and diagnostic-only storage remain explicit in the receipts.

## Timing and stopping decision

- Complete smoke wall: **2,050.177 s (34.17 min)**; cold model load 60.668 s and
  adapter preparation 0.289 s separately. Preparation across both tasks took
  72.892 s; cache diagnostics 29.146 s and reset diagnostics 24.865 s, included in
  physical smoke wall, not added again.
- The measured 184-request selection-plus-confirmation projection was **5.47 h**,
  with an observed request-duration range of **4.70–6.61 h**, excluding cold loads
  and adding about 233 s for cache diagnostics. This was a workload forecast;
  that work was not admitted or scheduled.
- [Selection-budget provenance](selection-budget-receipt.json) derives a conservative
  3,559-second single-GPU residency bound for historical seed-47 SFT. One percent is
  **35.59 GPU-seconds**. It is allocated residency, not an active-time hardware meter;
  the historical executed Python commit is not pinned by the training receipt.
- The implementation's eight-request selection envelope was 782.517–843.332 s.
  Admission therefore stopped before model loading, with zero selection GPU time,
  no selected candidate and no confirmation-population read. This is an empirical
  scheduling estimate, not a mathematical impossibility proof or a rejected rule.
  The estimator was implemented after the original protocol freeze and pinned by
  the stage lock before selection; it uses timing only, never smoke semantic scores.

Earlier failures are retained: attempt 01 completed one base request before a scoped
operation-registration failure; attempt 02 completed nine requests before an adapter
projection-shape failure. Their measured smoke intervals were 92.681 s and 831.936 s,
plus separate cold loads. The four-token unscored adapter integration probe took
75.694 s including loading and cleanup. These costs are not erased by attempt 03.
The report lists all recorded intervals; it is not a complete meter of engineering,
conversion CPU work, historical data preparation or idle residency during repairs.

## Verifier repair and evidence provenance

Attempt 03 initially used the frozen historical browser verifier. Its automatic
pipeline layout omitted unused binding 1, but the harness still supplied all four
contract buffers. This falsely blocked a valid unary adapter shader. The
[versioned repair](contract_browser_verifier.mjs) supplies an explicit contract layout;
parser, numeric checks, tolerances and canaries are unchanged. Historical bytes remain
untouched. [Focused qualification](layout-repair-smoke-qualification.json) accepted a
correct unused-binding shader and both smoke references, and rejected wrong arithmetic.

Every completed model output/token sequence was sealed before [public replay](public-replay-03.json)
on the same Jupiter browser adapter. The [seal](public-replay-03-seal.json) binds all
sources, sample order and verifier identities. Replay took 0.757 s, including 0.392 s
browser startup, and added zero model requests. Only public receipts and their
verification-time contribution changed; k remained 2, and only the existing samples
could be ranked. Original failures and costs remain in [raw smoke 03](native-smoke-03.json).
This is explicitly mixed provenance: original model generation plus separately
recorded repaired verification, not a silently rewritten monolithic run.

[Runtime lock 03](native-runtime-lock-03.json) binds generation. [Stage lock 03](native-stage-lock-03.json)
binds the original generation, replay, repaired verifier and admission code. The
[original protocol](protocol.json), [freeze](protocol-freeze.json) and
[pre-model amendment](protocol-amendment-01.json) preserve candidates, splits,
thresholds and generation settings. The amendment separates fixed smoke cost from
candidate-selection cost; all settings-selection work remains charged.

## Runtime safety and reproducibility

The [service-window receipt](service-window-summary.json) records 1,021 allowed
observations, no admitted provider work and at least 78.95 GiB available RAM. The
existing provider stayed active with the same main PID and zero restarts. Our owned
model/browser processes exited and our read-only monitor was stopped. No live service
was reset, stopped or updated; Jupiter's dirty Doppler checkout was preserved.

The converted artifact passed all 267 shard hashes and 19,261 source-to-F16 scalar
samples across 427 text tensors. Known-reference qualification passed 22/22 shaders
and 286/286 checks; those are reference tests, not model confirmation. Focused native
operator, lifecycle, orchestration, timing, replay and reporting checks are recorded
with their implementation commits. Model weights were not downloaded.

Rebuild this report from Gamma without model or oracle execution:

```sh
python3 projects/distillation/wgsl/channel_gain/report_native_smoke.py \
  --smoke projects/distillation/wgsl/channel_gain/native-smoke-03.json \
  --public-replay projects/distillation/wgsl/channel_gain/public-replay-03.json \
  --attempt projects/distillation/wgsl/channel_gain/native-smoke-01.jsonl \
  --attempt projects/distillation/wgsl/channel_gain/native-smoke-02.jsonl \
  --integration-probe projects/distillation/wgsl/channel_gain/adapter-probe-03.json \
  --selection projects/distillation/wgsl/channel_gain/native-selection-03/selection-receipt.json \
  --json-output projects/distillation/wgsl/channel_gain/results-03.json \
  --markdown-output projects/distillation/wgsl/channel_gain/RESULTS-03.md \
  --label 'Attempt 03 with sealed public-verifier repair' --overwrite
```

A confirmation study would need a separately frozen feasible execution plan; this
run does not relax its cap or borrow smoke outcomes as confirmation. The broader
[nine-rung roadmap](../RECONFIGURATION-ROADMAP.md), [shared standard](../EXPERIMENT-PROTOCOL.md),
[registry](../EXPERIMENTS.md) and [template](../EXPERIMENT-TEMPLATE.md) remain separate
from this run's immutable records.

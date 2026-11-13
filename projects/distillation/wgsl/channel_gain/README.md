# First prefill channel-gain experiment

**Completed and evaluated, 2026-11-13: no shader-improvement confirmation.**
The full eight-request selection and 176-request confirmation workload ran.
The selected `gain-negative` rule scored **0/16** confirmation tasks in both
MLP/base-cache and MLP/re-prefill arms. Same-prompt base, public-selected best-of-2
base, shuffled context, random state and permuted gains also scored **0/16**.
The trained seed-47 adapter scored **11/16**. These are completed confirmation
results, not smoke scores or a budget-only stop.

The failure boundary matters: **all 160 non-adapter outputs failed the required
source contract before compilation**, all missing `WORKGROUP_SIZE` (one also
missing the compute annotation). All 16 adapter outputs compiled and dispatched.
This measures failure to produce compliant shaders; the untrained arms did not
reach an executed numeric-accuracy comparison. Their shared zero floor limits
what these tasks can reveal about changes in numeric shader behavior. The
[independent confirmation audit](CONFIRMATION-AUDIT-04.md) records that boundary.

The [final report](CONFIRMATION-RESULTS-04.md), [machine-readable results](confirmation-results-04.json),
[authenticated evidence](confirmation-evidence-04.json) and
[byte-preserving archive](archive-04/archive-manifest.json) are the current evidence.
[execution-status.json](execution-status.json) records the completed state.
The [continuation policy](protocol-continuation-02.json) and
[stage lock 04](native-stage-lock-04.json) preserved the original candidates, tasks,
controls, k=2 and hidden-test separation; the 1% setup target was scored rather
than used to stop execution.

## Confirmation outcome and limits

All 16 task families were evaluated under seven conditions and both cache arms.
Base and adapter samples were shared between arm comparisons; the total is
176 unique generations, not 224 separate generations. Semantic success requires
both public checks and all 12 confirmation checks. The adapter's hidden-only
score was 12/16, but its semantic score is 11/16. Wrong acceptances were zero in
every condition; zero wrong acceptances does not make an incorrect shader correct.

Gain versus each control had zero wins, zero losses and zero discordant tasks.
Prompt-dependence tests therefore remain **underpowered**, not proof of equality.
The adapter-minus-matched-base gap was 11 tasks; gains closed **0%**, failing the
frozen gap-closure criterion. Both cache arms' joint decisions are
**not_confirmed**. This result applies to the first selected rule and measured
implementation, not all transform families or the reconfiguration architecture.

Sixteen same-prefix diagnostics reused identical frozen gain hashes between cache
arms. Every task showed a KV difference at layer 31 only; earlier KV layers and
all 24 recurrent layers matched. Logit relative L2 ranged from 0.000818 to
0.001880, with no top-1 changes. All-projections remains **not applicable**.
The two exact base-logit reset checks described below belong to smoke 03; they
are not 16 new confirmation reset tests.

## Measured costs and environment

- Selection used **822.030 seconds** of single-device residency against the
  unchanged **35.59-second** target: **23.0972%** of the conservative 3,559-second
  historical SFT denominator, versus the required 1%. No offline training ran.
- Added attributed E2E latency, computed as gain total / same-prompt base total
  minus one, was **11.69%** for base cache and **25.34%** for re-prefill. Both
  exceed the 10% target. These are the frozen ratios of totals, not averages of
  per-task percentages or isolated speed measurements.
- Full best-of-2 base sample cost was **1.844x** the base-cache gain cost and
  **1.643x** the re-prefill gain cost. Both samples are charged; integer rounding
  is not exact compute matching.
- Selection physical stage time was **884.248 seconds**; confirmation physical
  stage time was **16,729.217 seconds (4.647 hours)**. Together they took
  **17,613.465 seconds (4.893 hours)** before final receipt serialization.
  Confirmation included 176 requests, 587.799 seconds of preparation and
  232.854 seconds of cache diagnostics. Cold loads are already inside stage
  times; do not add these components again. Prior failed attempts and smoke
  costs remain below and in the historical reports.
- Base-cache retained increment was **131,072 bytes**, but its isolated incremental
  peak is **unproven**. Re-prefill retained **326,201,344 bytes**, exceeding the
  **232,821,904-byte** cap even without claiming a peak measurement.

The [environment ledger](environment-04.jsonl) records the owner-authorized
retirement of the idle Reploid provider and the parallel 27B screen from
**13:01:51.789 to 13:12:31.783 UTC**, a **639.994-second** overlap. Timing is
**contended**. Main-request UTC boundaries were not recorded, so no exact
per-request phase allocation or causal speed comparison is inferred. Quality
outputs and denominators were retained unchanged. Historical SFT residency is a
conservative lower bound rather than an active GPU counter; historical data and
engineering preparation costs are not fully metered.

## Runtime closure

[Closure evidence](closure-04/closure.json) records both the completed 9B study
and deferred 27B probe receipts. All 2,683 live guard observations before the
intentional monitor stop allowed execution; the final row records that stop.
The retired provider was inactive/dead with PID zero and zero restarts. No
processes matching the private experiment paths or named guard remained at the
16:30:06 UTC observation; this is a scoped process check, not a global GPU audit.
The exact guard history is compressed with raw and archive hashes in the closure.

## Historical attempt 03: smoke and admission stop

The remainder records the earlier smoke-only outcome. Its claims about untested
candidates, unevaluated confirmation and service preservation apply to attempt 03,
not the completed continuation above. Original reports and receipts remain intact.

**Historical attempt 03 closed at selection admission, 2026-11-13. No shader-improvement confirmation.**
The complete two-task smoke and corrected public replay ran. The eight-request
selection workload was not admitted under the unchanged 35.59 GPU-second cap;
at that point both candidates were **untested**, with no winner and no confirmation requests.
This outcome applies to this implementation and budget, not every gain rule or
reconfiguration architecture.

The historical attempt-03 state is retained in [RESULTS-03.md](RESULTS-03.md). Detailed
request, cost, cache, reset and memory tables are in [RESULTS-03.md](RESULTS-03.md)
and [results-03.json](results-03.json). The [selection receipt](native-selection-03/selection-receipt.json)
is the historical admission decision source of truth.

### What ran and what it showed

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
trained-adapter gap closure and wrong-acceptance criteria were unevaluated on confirmation at that smoke-only stage. The full best-of-2 base samples consumed 1.77x and 2.04x the primary gain
request's attributed compute; base-favoring integer rounding is reported, not exact
compute equality.

Mean paired added latency was 9.13% for base cache and 23.33% for re-prefill. Output
lengths differed: base averaged 278.5 tokens and actual gains 270.0. These descriptive
smoke observations do not pass or fail the confirmation latency criterion. Timing
includes token preparation, reference/base prefill, gain derivation, snapshot
restoration or re-prefill, decode, request cleanup and public verification. Shared
setup is charged back to each arm; physical batch wall time is reported separately.

### Cache, reset and memory

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

### Timing and stopping decision

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

### Verifier repair and evidence provenance

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

### Runtime safety and reproducibility

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

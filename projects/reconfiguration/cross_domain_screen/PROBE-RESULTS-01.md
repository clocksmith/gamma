The deferred 27B WGSL probe completed four generations and two reset checks on
2026-11-13. Base and channel gain each scored **0/2** on the original public
checks. All four responses failed the response/interface contract before shader
compilation, dispatch or numerical execution. This exposed-task probe observed
no gain advantage; it is not confirmation or a measurement of numerical shader
correctness.

| Exposed smoke task | Condition | Tokens | First rejected boundary | Physical request | Charged native total |
| --- | --- | ---: | --- | ---: | ---: |
| Sign bit | Base | 255 | Required override declaration not recognized | 84.204 s | 84.213 s |
| Sign bit | Gain | 260 | Required override declaration not recognized | 74.694 s | 95.078 s |
| Tent | Base | 252 | Forbidden Markdown fence | 83.340 s | 83.345 s |
| Tent | Gain | 252 | Forbidden Markdown fence | 73.442 s | 93.754 s |

The sign-bit parser diagnostic was
`required_override_absent:WORKGROUP_SIZE`. Both exact sources contain
`override const WORKGROUP_SIZE ...`; the name was present, but the parser did not
recognize that form as the required override declaration. Describing this merely
as an omitted name would be inaccurate. Both tent responses contain a
Markdown code fence tagged `wgsl` and are identical in source and token IDs. The sign-bit pair
differs in source and tokens. No response was repaired or rescored, and no shader
reached compilation or numerical checks. The paired pass/fail result is zero
wins, zero losses and two ties. No output reached the 768-token cap.

The probe used the provisioned `Qwen/Qwen3.8-27B` artifact, active manifest
`e29626a8d3c41c0af8c0dd945d028464dcebfef2413ba85e4f5e8695d5910d06`, with
the fixed analytical negative-gain rule mapped to dense MLP layers 62/63:
beta −0.05, clip 1, epsilon 1e−6 and reference A. Only base and actual gain in the
base-cache arm ran; there were no additional controls, adapter or re-prefill arm
in this probe. Its first token uses base-prefill logits. The two existing exposed
smoke prompts contain 593 and 592 tokens. The shorter 24-request cross-domain
screen and its known neutral corrected outcomes were recorded before this probe;
the candidate was not retuned. The [frozen probe lock](probe-runtime-lock-02.json)
binds the protocol, runtime, artifacts and repaired explicit-layout verifier.

Both discard/reset diagnostics reproduced all 248,320 baseline logits exactly:
relative L2 and maximum absolute difference were zero, with unchanged top-1.
The gain and adapter were absent and sequence length was zero before each reset
prefill. This supports serial reset correctness on these two prompts, not
concurrent full-model isolation. The longer full-prefill path completed without
a recorded runtime or device failure; it does not qualify arbitrary long contexts.

Cold model load took **75.780 s**; generation, preparation, resets and public
scoring took **377.053 s**; cleanup took **0.046 s**. The observed model-load-start
to cleanup-end interval was **453.167 s**, from 16:21:11.925 to 16:28:45.092 UTC.
Preparation totaled 40.682 s and reset diagnostics 20.581 s. Public parser checks
took 0.677 ms; there was no shader-dispatch cost because every source was rejected
first. Physical request totals were 167.544 s for base and 148.136 s for gain.
Including required preparation, token-contract handling and owned cleanup, the
charged native totals were **167.558 s for base and 188.832 s for gain**, a
12.70% increase across these two samples. Response lengths differ on one task;
these totals do not establish a general latency ratio.

Each transformed request retained 139,264 logical gain bytes in 262,144 allocated
bytes. Matched-baseline subtraction likewise measured 262,144 incremental retained
tensor bytes. Device GPUBuffer high-water reached 20,763,086,984 bytes; this includes
model, cache, pooled temporaries and diagnostic storage, and is neither incremental
gain memory nor physical-RAM consumption.

The scheduler waited 9,433.453 s for the original 9B completion prerequisite and
exclusive timing-lock admission; this wait is separate from model execution. It
validated the self-hashed 176-request 9B receipt, acquired the cooperative exclusive
lock at 16:21:11.106 UTC, and rechecked the fresh inactive/dead/PID-zero provider
guard. Node exited with code zero at 16:28:45.434 and the lock was released. The
probe therefore ran after the 9B completion gate under exclusive cooperative
admission. Global GPU isolation remains unqualified; the lock alone does not
exclude processes that ignore it. No service changes or GPU recovery occurred in
the probe wrapper.

[Archive](probe-archive-01/archive.json) preserves five complete raw files as
byte-verified gzip: 22,542,033 original bytes and 612,292 stored bytes.
[Validation](probe-archive-01/validation.json) checks the canonical receipt and
output identities, four completed requests and scoring strictly after the seal.
[Audit](probe-archive-01/audit-summary.json) retains failure stages, exact source
hashes, paired outcomes, timing and memory; the
[summary](probe-archive-01/summary.json) also includes every submitted source and
both reset receipts. No additional model calls or shader dispatches were used to
prepare this report.

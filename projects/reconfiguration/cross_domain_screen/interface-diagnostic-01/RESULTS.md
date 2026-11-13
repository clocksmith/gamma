# Explicit-interface diagnostic: executable shader baseline restored

The provisioned 27B model passed **2/2 exposed shader tasks with base and 2/2
with unchanged channel gains**. Every output compiled, dispatched on the GPU,
matched the original public numerical checks and preserved buffer guards. In the
prior [unscaffolded probe](../PROBE-RESULTS-01.md), both conditions scored 0/2 at
the source-contract boundary. This is a prompt/interface repair, not a gain win.

Both conditions received the same valid WGSL scaffold, including the required
workgroup override, bindings, bounds guard and output index. The expression was
left as a marked `0.0` placeholder. The model supplied `select(1.0, -1.0, x < 0.0)`
and `max(0.0, 1.0 - abs(x))` for the two tasks. The supplied placeholder scaffold
itself compiled and dispatched but failed both public numeric checks before any
model load, showing that the interface was valid and the answers were not supplied.
No output was repaired, no Markdown stripped, and no check changed.

| Task | Base | Gain | Tokens, base/gain | Base/gain output |
| --- | --- | --- | ---: | --- |
| Sign bit | Pass | Pass | 242/242 | Identical source and token IDs |
| Tent | Pass | Pass | 238/238 | Identical source and token IDs |

The same negative gain rule, layers 62/63, beta −0.05, clip 1, epsilon 1e−6,
reference A, base-cache behavior, sampling settings and 768-token limit were
preserved. Exact prompt/reference token spans were qualified with the provisioned
tokenizer. All four outputs were sealed before scoring. Two subsequent serial
reset checks reproduced all 248,320 logits exactly. The three focused existing
probe execution/verifier tests passed before launch.

The diagnostic's predeclared readiness criterion was reached: both base outputs
compiled and dispatched, and at least one passed numerically. The two tasks were
already exposed, and both are now solved; they cannot establish improvement on
fresh tasks or discriminate this gain rule. No hidden confirmation checks were
read. The completed original confirmation and its scores remain unchanged.

Cold load took 75.758s; execution, preparation, reset and
scoring took 326.770s; model load through cleanup took
**402.920s (6min43s)**. Charged native request totals
were 151.082s for base and 162.415s for gain, **7.50%**
more for gain across these two samples; public verifier costs are separate in the
receipts. This is descriptive two-task accounting, not a qualified efficiency win.
The run acquired the cooperative exclusive GPU timing lock. Global device isolation
was not independently established. The model process exited, the owned guard was
stopped, and the retired provider remained inactive/dead with PID zero.

[Protocol](protocol.json), [runtime lock](runtime-lock.json), [prompts](prompts.jsonl)
and [scaffold](scaffold.wgsl) were committed before generation in `d31eb0a02`.
[Summary](evidence/summary.json) retains exact sources, scores, timings and reset
receipts. [Archive manifest](evidence/archive.json) preserves eight complete raw
files with compressed and uncompressed byte hashes. Local verification checked
all archive hashes, canonical receipt/output hashes, all four scored-source hashes
and scoring after the four-output seal. The archive contains 96 guard observations;
all 95 live observations allowed execution, followed by intentional monitor stop.

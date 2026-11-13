# Six-family channel-gain screen

This **frozen exploratory screen completed all 24 requests** on 2026-11-13.
The [original report](RAW-RESULTS-01.md) and [raw archive](screen-run-01/archive.json)
retain generation, scoring, timing and reset evidence. Base, channel gain and
shuffled context each passed 4/6, with no paired gain advantage. The original
permuted 3/6 includes a restricted-interpreter rejection: its unchanged function
passes all six cases in ordinary Python. A versioned oracle repair and all-output
replay are pending; the original scores remain historical evidence.
It reuses the selected `gain-negative` MLP formula without candidate tuning,
mapped prospectively from the original 9B model to the provisioned 27B model. The
original [WGSL experiment](../../distillation/wgsl/channel_gain/README.md) and
its confirmation remain separate.

[protocol.draft.json](protocol.draft.json), whose retained filename records its draft history, now freezes six fresh task families,
one sample per task under base, actual gains, shuffled context and permuted gains:
24 generated outputs. Only MLP/base-cache runs are included. All-projections is
inapplicable to this rule. Three separate prefill-only reset diagnostics check
one task per domain. No efficiency score vetoes completion of this fixed screen.

| Domain | Families | Output |
| --- | --- | --- |
| Arithmetic | Exact rational expressions; simultaneous congruences | Three-integer JSON arrays |
| Short Python | Adjacent run lengths; closed-interval intersection | One function |
| Structured text | Filter/order/project records; escaped delimiter decoding | JSON arrays |

These are six independent problem-family units, with one concrete prompt each.
Python case variants are within-family checks. This screen cannot establish broad
coding, arithmetic, writing or general transfer. Tasks were authored after WGSL
candidate selection; prior model-training exposure is unknown.

The source candidate's beta, clipping, epsilon and reference construction stay
fixed. Its last-two-layer choice maps from 9B layers 30/31 to dense 27B layers
62/63. The original candidate and the mapped candidate have distinct recorded
identities. Changing model and domains together means this screen cannot isolate
cross-domain transfer on the original 9B model. Gains are derived afresh from each request; shader gain arrays are not
reused. Base-cache emits its first token from unchanged base-prefill logits.
Multi-token answers exercise later transformed decode. The frozen 256-token cap
is smaller than the shader cap; every truncation and termination reason must be
reported, with capped outputs retained in the denominator.

`runner.mjs` and its tests pin provisioned
model/tokenizer/template, exact source identities, runtime/device and task/oracle
bytes before generation. CPU token-boundary qualification passed all six
instruction spans. The [runtime lock](screen-runtime-lock-01.json) bound final
settings and exact bytes before execution. No prompts, models or samples were
replaced after observing quality.

## Scoring boundary

All 24 exact outputs are journaled and sealed before **any** public or heldout
score. The generator receives only task prompts and their visible examples.
The evaluator's reserved answers/cases are not a generation or selection input.
This is procedural separation, not a claim that the evaluator's source is secret
from repository readers. There is no model candidate search or best-of-k selection.

`oracles.py` accepts strict raw JSON or a single Python function. It does not strip
Markdown, repair answers or execute generated Python using `exec`/`eval`. A bounded
AST interpreter implements the declared language subset with step, integer and
container limits; unknown syntax and calls fail. Public checks are JSON schemas
or visible Python examples. Heldout checks compare exact answers or additional
behavior cases, including empty inputs, distinct runs, touching interval endpoints
and negative values. Semantic success requires both public and heldout success;
wrong acceptance means public success with heldout failure.

```bash
python3 projects/reconfiguration/cross_domain_screen/test_oracles.py
echo '{"taskId":"arithmetic-fractions","source":"[313,86,59]","phase":"both"}' \
  | python3 projects/reconfiguration/cross_domain_screen/oracles.py
```

The CLI also accepts `--task-id ID --source-file PATH --phase public|heldout|both`.
It returns JSON containing `passed`, `publicPassed`, `heldoutPassed` and individual
check results. Per-phase invocations omit the unrequested phase field. Correct
reference fixtures and plausible errors qualify the evaluator, not the model.

Report raw paired outcomes, token counts, truncations and errors. Keep cold load,
statistics/preparation, per-request attributed costs, physical stage time, reset
diagnostics and scoring costs separate. Unknown memory peaks remain unknown.
The omitted trained adapter, matched-compute sampling and re-prefill arms mean
this screen supports neither specialization-efficiency nor cache-comparison claims.

The process borrows bounded matched tests, frozen identities, sealed evidence,
full costs and preserved failures from the archived
[enwiki9 workflow](../../enwiki9/ADAPTIVE_WORKFLOW.md). It does not reopen that
project or import its compression targets. The prospective
[experiment standard v2](../../distillation/wgsl/EXPERIMENT-PROTOCOL.md) governs
this new screen; its content hash is recorded in the draft protocol.

The completed execution used the six short prompts (89–164 tokens); responses
were 14–128 tokens, with no output-cap hits. Three sequential full-model reset
checks reproduced all baseline logits exactly. The 639.994-second load-through-
cleanup interval overlapped the original 9B job, so timing is contended. The separate
593/592-token WGSL probe remains unexecuted while the original 9B study is active,
because a longer unchunked 27B prefill previously caused device loss. Short-prompt
execution does not qualify that longer path. The original 9B confirmation remains
active (59/176 observed at 13:19:17 UTC on 2026-11-13), with no quality conclusion.

Separate [Mac synthetic checks](https://github.com/clocksmith/doppler/blob/daede6a0/reports/channel-gain-20261113/synthetic-isolation-receipt.json)
exercise two live gain states and reset/failure cleanup on tiny shared tensors.
They establish neither full-model concurrent switching nor cross-domain quality.

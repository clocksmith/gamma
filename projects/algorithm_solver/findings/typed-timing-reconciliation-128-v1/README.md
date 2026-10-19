# Reconcile accepted-answer losses and diagnose execution cost

The fall from 4/10 to 2/10 structural answers and 8/10 to 4/10 nearest-graph
answers is entirely explained by fresh total-budget rejection of previously
correct programs. The lost programs have identical source hashes and still pass
their recorded independent checks. Fresh embedding alone exceeded two seconds
for every loss; their public sandbox executions never started. There is no new
correctness loss among these six arm-level losses (five distinct requests).

The [rejected literal candidate](../typed-literal-margin-fit-128-v1/README.md)
remains rejected. No solver candidate was rerun or rescored here. No historical
latency was substituted into a fresh result. The only implementation change
removes reproduced process-wait polling overhead, separately measured below.

## Exact losses

| Arm | Request | Old complete seconds | New complete seconds | New embedding seconds |
| --- | --- | ---: | ---: | ---: |
| structural_control | lcd:1512 | 0.681 | 2.232 | 2.203 |
| structural_control | lcd:1051 | 1.112 | 3.612 | 3.605 |
| nearest_training_graph | lcd:1051 | 1.108 | 3.607 | 3.605 |
| nearest_training_graph | lcd:1046 | 1.104 | 3.189 | 3.187 |
| nearest_training_graph | lcd:2144 | 1.572 | 4.779 | 4.773 |
| nearest_training_graph | lcd:1489 | 1.674 | 3.974 | 3.970 |

Structural retained lcd:1748 and lcd:252. Nearest retained lcd:1748, lcd:1464,
lcd:1710 and lcd:252. Nearest lcd:1512 remains semantically wrong on the recorded
suite; lcd:1101 was already over budget historically and remains over budget.
The historical and newer structural configurations differ by the interior-empty
option. That difference explains lcd:1464 becoming valid but wrong, not an answer
loss. For lcd:1046 the newer structural repair cannot finish within its expired
deadline; it was previously valid but incorrect. Neither was previously accepted.

## Per-stage timing and gate semantics

All times below are seconds; old and new measurements are separate. Full phase
fields, public-start flags, source/graph equality and independent verdicts are in
[reconciliation.json](reconciliation.json). The old values come from the sealed
recovered comparison, the new values from the sealed literal experiment.

| Request | Embedding old / new | Prediction old / new | Structural old / new | Nearest old / new |
| --- | ---: | ---: | ---: | ---: |
| lcd:1512 | 0.631 / 2.203 | 0.0119 / 0.0260 | 0.681 / 2.232 | 0.667 / 2.205 |
| lcd:1748 | 0.670 / 1.354 | 0.0024 / 0.0027 | 0.710 / 1.395 | 0.706 / 1.388 |
| lcd:1464 | 0.804 / 1.821 | 0.0023 / 0.0970 | 0.931 / 1.975 | 0.838 / 1.855 |
| lcd:1051 | 1.073 / 3.605 | 0.0026 / 0.0035 | 1.112 / 3.612 | 1.108 / 3.607 |
| lcd:1046 | 1.068 / 3.187 | 0.0027 / 0.0031 | 1.117 / 3.198 | 1.104 / 3.189 |
| lcd:2144 | 1.537 / 4.773 | 0.0031 / 0.0253 | 1.576 / 4.801 | 1.572 / 4.779 |
| lcd:1710 | 1.158 / 1.849 | 0.0026 / 0.1427 | 1.196 / 2.001 | 1.192 / 1.886 |
| lcd:1101 | 2.213 / 5.194 | 0.0025 / 0.2055 | 2.219 / 5.402 | 2.215 / 5.195 |
| lcd:252 | 0.482 / 1.821 | 0.0024 / 0.0026 | 0.521 / 1.863 | 0.517 / 1.855 |
| lcd:1489 | 1.637 / 3.970 | 0.0030 / 0.0031 | 1.679 / 3.978 | 1.674 / 3.974 |

The two-second gate includes warm query tokenization/embedding, retrieval,
neural prediction for neural arms, construction, correction, deterministic source
assembly and the complete host public-judge call. The latter includes temporary
file preparation, process launch, namespace/interpreter/harness startup, execution,
output collection, cleanup and host verdict comparison. Nearest excludes predictor
cost. Residual bookkeeping is included in complete time even when it is not a
named phase. Shared inference is charged once to each arm, not rerun or double
counted. Prediction capture includes preserving logits; the newer capture also
preserves literal logits, so that measured overhead is charged.

Cold checkpoint load, encoder load, fit-memory embedding and warm-up are excluded
from the warm gate and reported separately. Old setup: 0.016 / 3.084 / 28.287 /
0.168 seconds respectively. New setup: 0.018 / 3.592 / 39.818 / 0.436 seconds.
Imports, asset verification and full cold application opening are not claimed by
those setup phases. Independent scoring is also separate and cannot change the
sealed public decision. The sandbox result wall clock begins before process
launch; the outer route timer additionally covers file preparation and cleanup.
No evidence of double-charged embedding or a false accepted answer caused by
budget accounting was found.

For lcd:1710 the newer structural prefix reached 1.992 seconds before construction
and public execution; the approximately 5.6 ms public call timed out and complete
time reached 2.001 seconds. Its unchanged source was independently wrong, so this
is not a lost correct answer. For lcd:1464, the structural prefix took 1.975
seconds and failed examples. The 0.25-second additional cap is only a ceiling:
the complete gate left about 25 ms, and preparation/validation left still less
for the sole extra public call. That call timed out at a recorded sandbox wall
of about 13.7 ms. It did not test a known literal-only defect. This explains why
the experiment cannot broadly evaluate literal search.

## Reproduced overhead and narrow fix

[Twelve harmless probes](sandbox-probe.json) observed the actual bubblewrap exit
using a host pidfd while retaining the old wait. Functional checks had exited
after roughly 21-27 ms but Python timed wait returned about 5-11 ms later.
Python Popen.wait(timeout) polls with exponentially growing sleeps. Six trivial
payload probes additionally observed Python payload entry after 13-15 ms; startup
is real cost, not all removable waiting. These observations are approximate
because observer scheduling has its own delay.

`algsolve/judge/sandbox.py` now waits for the same monitor process through a
kernel pidfd exit notification when supported, then reaps it normally. Unsupported
kernels use the old timed wait. The same timeout, namespaces, status-channel
verification, process-group cleanup and resource limits remain. Host descriptors
are created after launching the sandbox and are not passed to the payload. Real
elapsed route time remains charged. No interpreter, sandbox or payload is reused.

[Sixteen alternating synthetic functional checks](wait-comparison.json) measured
median total judge time 32.155 ms with polling and 24.791 ms with pidfd, a 7.364 ms
(22.9%) reduction in this probe. All checks passed. This is a software overhead
measurement, not a solving gain; it cannot recover any of the six embedding-driven
losses. The affected judge, lane, typed comparison and literal tests passed:
54 tests plus 5 subtests, including actual timeout and nonzero-exit behavior on
both normal and fallback paths. Changed Python files compiled and imported.

## Host contention: bounded conclusion

Existing Reploid Node workloads were active; they were not stopped or changed.
The newer monitor explicitly pins its process to CPUs 0-3, while the older runner
sets four PyTorch threads without imposing that affinity. Historical per-query
CPU time, cgroup throttle counters, run-queue delay and frequency were not recorded.
Therefore the fresh embedding slowdown (median per-case ratio 2.70) cannot be
exactly divided into contention, scheduling, CPU frequency and monitoring effects.

[An eight-call embedding-only probe](affinity-probe.json) alternated first-four
affinity and scheduler placement for the same exposed lcd:1051 input. Both kept
four CPU threads, the same 400% cgroup CPU cap and 8 GiB memory cap; no solver
decision or scoring occurred. Median pinned/unpinned times were 1.071/1.068
seconds, vectors were byte-identical and neither condition recorded throttling.
This does not reproduce the prior 3.605-second slowdown, and does not justify an
affinity change or a precise historical contention claim. The probe differs from
the full runner, including absence of fit-memory construction and its background
monitor. Host history cannot be reconstructed from this new snapshot.

## Literal mechanism: evidence without another execution

Using only the already exposed fit labels for post-score diagnosis, the fixed
margin order gives these exact-label positions. No target value was injected
into a solver. This comparison is diagnostic and cannot award a new solve.

| Request | Required bit edits | Required bit margin ranks | Exact-label proposal rank |
| --- | ---: | --- | ---: |
| lcd:1464 | 0 | none | outside search |
| lcd:1046 | 1 | 1 | 1 |
| lcd:2144 | 2 | 4, 1 | 8 |
| lcd:1710 | 2 | 1, 2 | 3 |
| lcd:1101 | 3 | 13, 1, 6 | outside search |
| lcd:1489 | 7 | 13, 2, 5, 29, 34, 1, 3 | outside search |

lcd:1464 has an operation/recipe error; its literals already match the selected
qualified label. lcd:1046 and lcd:1710 have their exact qualified label among the
first and third proposals. lcd:2144 requires proposal eight; validation and earlier
public passes can affect which proposals are executed, so proposal rank is not
an execution rank. The three- and seven-bit labels cannot be reached by a two-bit
candidate; some required bits also fall outside the eight-bit pool. Exact-label
reachability does not exclude other semantically equivalent solutions. These facts
distinguish latency-censored opportunities from representational/search limits.

## Next achievable path and approval boundary

First establish a stable execution envelope on the existing model: retain the
four-thread, 8-GiB, 5-GiB, two-second limits and collect per-query process CPU time,
cgroup throttle deltas and affinity alongside warm embedding and sandbox phases.
A separately named, bounded diagnostic should isolate full-run monitoring/setup
effects from host scheduling before any new quality pass. Do not discard the slow
run, replace it with favorable timing or rerun this rejected candidate unchanged.
The reproduced wait fix is ready; no additional CPU-placement change is supported.

Learned literal selection is not established as the immediate blocker: two
qualified labels already rank within the first three fixed proposals, and neither
received a trial. Broader multi-bit errors remain a model/representation or search
gap. The 74/15093 positive-bit imbalance remains a hypothesis, not a causal result.
No bound sweep or training follows from this diagnostic.

The existing [pending training proposal](../../contracts/typed_lcd_suby_training_proposal_v1.json)
requires explicit owner approval for one named 400-step CPU run: four threads,
8 GiB RSS, 5 GiB total assets/run disk, 900-second training-phase cap, seed 17,
width 64, two layers, AdamW at 0.001, fixed final checkpoint and no sweep, downloads
or new dependencies. Its rebuilt corpus hash is
`6c43031ed101199ab6cdae7a8377a301988ad83d8343ad84689ccccf7e4a5cd5`.
It is not the original-corpus literal-learning experiment, and its present loss
does not test balanced literal learning. Two overlength fit descriptions still
fail the no-truncation training preflight. An actual literal-learning proposal
must separately freeze its loss/encoding, exact original or rebuilt assets and
full-text input policy before approval; do not treat approval of the old proposal
as approval of those changes. No training or protected access occurred.

## Preservation and component boundary

The diagnostic checks all consumed input hashes before/after reading. Original
captures, rejected decisions, source suites and scores remain byte-identical.
Raw source/labels/tests remain ignored and local; this folder exports metadata.
The component intent and safety boundary are preserved. New sandbox source bytes
mean historical manifests cannot be resumed against the current tree; use their
original pinned runtime. No policy, model catalog or framework change was made.

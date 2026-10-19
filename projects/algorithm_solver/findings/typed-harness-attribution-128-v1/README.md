# Prepared harness timing attribution; execution blocked by contention

The requested fixed comparison is prepared, not executed. No new timing result,
quality claim, training or protected scoring was produced. No push occurred.

[Preflight](preflight.json) verified x@128, a clean starting main at 74e599026,
no loaded Gamma scopes and no orphan Gamma work. Four separate Reploid workers
remain active: PIDs 2707, 2709, 2711 and 8273. Their two-second CPU tick deltas
sum to 994 ticks, about five cores at the host's 100 ticks/second. CPUs 1 and 2
were approximately 53% and 80% busy during that sample. Sequential Gamma work
alone would not make the requested runs uncontended.

The user has been asked whether these separately serving workers may be paused
briefly and restored. No signal or affinity change was sent to them. The runner
refuses to execute while the recorded same-identity workers remain active. If an
owner stops them independently, recheck process identities, orphan work and CPU
load before launch. A temporary pause, if approved, needs an outer supervisor
that restores exactly the originally running workers in a finally block and on
termination; retain a before/after receipt. Do not pause replacements with reused
PIDs or infer permission from this protocol.

[The fixed protocol](protocol.json) specifies one pass through each of three
separate sequential processes: embedding-only; full inference/capture with the
original monitor; and identical full inference/capture without that monitor.
This isolates relevant setup and monitoring effects before route execution,
because the historical embedding slowdown occurred during capture, before public
decisions or scoring. All three use the same ten frozen fit queries, original
assets, tokenizer behavior, four threads and CPUs 0-3. Cgroup caps remain four
CPUs and 8 GiB; disk is capped at 5 GiB. The overall cap is 300 seconds with at
most 120 seconds per arm, including preservation of a timeout or failed arm.
There are no repeats or condition sweeps. Query embeddings are freshly computed;
none are read from a cache for an end-to-end claim.

The runner records each stage, process CPU time, cgroup throttling, thread runnable
delay, monitor-thread CPU time, affinity, vector hashes and full-arm raw prediction
parity. Captures/logits go only into ignored runs. It does not load independent
tests, execute solver candidates or produce quality scores. Model cold setup and
warmup are recorded separately. The two-second complete-route gate is unchanged.

Only a measured reproducible harness overhead defect can lead to a minimal fix,
focused tests and the one newly authorized corrected candidate/control comparison.
That later comparison must retain fresh complete timings, all failed attempts and
sealed decisions before independent fit scoring. Otherwise stop with a precise
unresolved cause and next proposal; do not chase a favorable timing sample.

`run_arm.py` compiled, imported, and its CLI help ran. These checks do not validate
execution behavior or establish timing attribution. The prior rejected run and
all its evidence remain unchanged. Run the prepared script only after the
uncontended precondition is actually met and the launch protocol is sealed.

## Read-only interruption assessment

[Worker identities](worker-inspection.json), [service state](service-inspection.json)
and the [unarmed restoration plan](restoration-plan.json) were captured without
pausing workers or starting timing. The four processes belong to x (UID 1000).

| Node PID | Service | Parent | Start ticks since boot | Role |
| ---: | --- | ---: | ---: | --- |
| 2707 | reploid-qwen-08b.service | 2569 | 35519 | Whole-model 0.8B contributor |
| 2709 | reploid-qwen-27b-split.service | 2569 | 35519 | 27B partition contributor |
| 2711 | reploid-qwen-2b.service | 2569 | 35519 | Whole-model 2B contributor |
| 8273 | reploid-qwen-27b.service | 8266 | 38553 | Whole-model 27B contributor |

PID 2569 is the user systemd manager; PID 8266 is the flock wrapper and service
main PID for the whole-model 27B worker. Neither parent is a pause target. The
workers are active user services with no configured systemd watchdog and zero
recorded restarts. Three restart on failure; the split service has Restart=no.
SIGSTOP does not terminate a process, so it does not itself trigger those restart
policies. Executable and command hashes, boot ID, start ticks, UID, cgroup and
working directory are recorded for immediate revalidation after approval. No
identity-file contents, prompts, outputs or credentials were read or recorded.

The split worker's latest inspected status at 2026-10-19T09:17:19Z was ready,
offering, with zero active reservations, zero attempts and zero unsettled owners.
That is a time-stamped snapshot, not a guarantee of present idleness. The three
whole-model workers did not expose equivalent current request counts in the
inspected journal. All four have ongoing peer traffic, including existing invalid
message and send failures. Those errors predate any proposed pause. Active
requests cannot be ruled out from these observations.

Previously measured phase totals imply 100.25-182.11 seconds for one embedding-only
and two full capture passes, before process-launch, asset verification, telemetry
and publication overhead. A practical expectation is roughly two to three minutes,
with uncertainty from the very slowdown under investigation. This is a measured
phase projection, not a guaranteed completion time. The comparison remains capped
at 300 seconds; each arm at 120 seconds. No repeated passes are authorized.

The restoration design has a separate 330-second deadline, outside the benchmark
scope, armed and acknowledged before the first pause. It uses validated pidfds
rather than numeric PID signals, restores on supervisor pipe closure or expiry,
and is backed by supervisor finally/SIGINT/SIGTERM cleanup. The benchmark must
terminate within its 300-second limit plus ten-second cleanup allowance. Only
originally eligible Node workers are restored; service managers and wrappers are
untouched. Reused or replacement identities abort the operation. Verification of
all threads stopped and quiet CPU activity precedes any benchmark. Afterward,
process state, identity and service/peer health must be checked before disarming
restoration. This is a recorded design, not a running watchdog or executed pause.

A pause freezes admission handling, network callbacks and the two-second
participant poll. Memory, GPU allocations and flock locks remain held. Existing
settings include a ten-second control-channel timeout, thirty-second connect
timeout and 300-second execution-channel timeout. A two-to-three-minute pause can
therefore fail in-flight control operations and cause peer disconnections; a
near-cap pause can also exceed execution deadlines. Resuming scheduling does not
promise recovery of the interrupted requests. No graceful drain was performed or
claimed, and no service-policy changes or automatic restarts are authorized here.

During preparation, numeric capture discovery was tightened to exclude
`capture-seal.json`; all ten numeric inputs were verified without running the
model. Compilation passed. This preparation fix is not evidence of the historical
embedding slowdown and does not trigger the conditional quality comparison.

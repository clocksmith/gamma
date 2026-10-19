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

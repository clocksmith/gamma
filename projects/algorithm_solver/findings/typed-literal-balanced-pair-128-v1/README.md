# Approved paired literal-loss experiment: candidate rejected

The user approved both fixed 400-step arms. Both completed, with identical fresh
initial tensors and full untruncated 2,048-token CPU float32 inputs from the original
15 fit graphs / ten consumed fit problems. No audit or protected request was scored.
The balanced objective was not selected or connected to the editor.

| Route | Control correct / 10 | Balanced correct / 10 | Control wrong | Balanced wrong |
|---|---:|---:|---:|---:|
| Raw parallel | 5 | 0 | 0 | 1 |
| Frozen guard | 6 | 1 | 0 | 2 |
| Matched nearest graph | 6 | 6 | 0 | 0 |

The candidate lost five correct answers in each neural route. Guard p95 was
2.776 seconds for control and 3.872 seconds for balanced. Neither latency gate
passed. The nearest source was independently correct on nine cases, but only six
were returned within the full deadline. No infrastructure failures occurred in
scoring. Whole-literal diagnostics remain separate from executable correctness.
These are consumed-fit development results, not unfamiliar-composition evidence.

Control checkpoint: `ee879b9453fa3851b1c708fcff6dca96ace95d201081cfa5b504ed2d26fc3403`.
Balanced checkpoint: `4683c310c5bba91c238be99bcbb4456363a9b401f5feade35660fa7fa30f0fe6`.
The original recovered checkpoint and all previous evidence remain intact.

## Preserved failures and completed scoring

Training and all twenty fresh-query captures completed before the runner tried
to rewrite immutable `setup.json` with evaluation setup timings. That write was
rejected; no public decision or independent scoring had run. A separately sealed,
scoring-only continuation reused every complete capture and charged its measured
inference cost. It made no optimizer step, encoder call or new query inference.
All sixty public decisions were sealed before independent tests were read.

The continuation completed all twenty score records, then hit a variable-name
error in its final integrity/report statement. `report.py` verifies the complete
original source, checkpoint, capture and public-decision identities and rebuilds
only the aggregate from those immutable score records. No scores were rerun,
replaced or selected. Both failures are retained; these were receipt/report
failures, not successful uninterrupted runs. The second encoder setup timing was
not committed before failure and is unavailable; it is not invented.

Training phases took 9.555 and 9.879 seconds. Recorded training/inference plus
scoring phase wall time was 128.045 seconds, excluding initial imports/hash checks
and report rebuilding; outer execution timeouts bounded the combined work below
the approved 2,400 seconds. Peak monitored process-tree RSS was 5.188 GB and final
referenced assets/run disk about 1.354 GB. Training/inference used four CPU threads;
public decisions and scoring used two, identically for both arms. The watchdog's
legacy counters field reports four threads, while the preserved affinity and
launch scope show two for continuation. No GPU training, installs or downloads.

[Summary](summary.json), [raw artifact manifest](artifact-manifest.json),
[approved scope](../typed-literal-objective-proposal-128-v1/OWNER_APPROVAL.md).
The prior measured GPU guard remains the editor's explicit development composer;
this new candidate supplies no promotion or expanded search authority.

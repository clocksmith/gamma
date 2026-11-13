# Deferred 27B exposed WGSL probe

This remains an unexecuted four-generation mechanics and baseline-quality probe:
base and fixed negative gain on each of the two previously exposed WGSL smoke
tasks, plus two reset-prefill diagnostics. The output cap remains 768. All four
outputs are sealed before the original public shader checks, using the qualified
explicit-layout verifier repair. There is no candidate tuning or confirmation.

The probe protocol records the 24 completed 27B cross-domain requests and their
known neutral corrected outcomes. It has seen zero outputs from this probe. The
separate probe configuration changes only the execution-context description;
the completed screen's locked configuration and sources remain unchanged.

Root must review the source and create `probe-runtime-lock-02.json` before launch.
The lock includes the wrapper, completion gate and exact schedule, as well as the
probe/runtime sources, model assets, inputs and complete repaired-verifier identity.
From the private Gamma snapshot on Jupiter:

```sh
node projects/reconfiguration/cross_domain_screen/probe.mjs \
  --action lock \
  --protocol projects/reconfiguration/cross_domain_screen/probe-protocol.json \
  --config projects/reconfiguration/cross_domain_screen/native-jupiter-27b-probe-config.json \
  --tokenizer-preflight projects/reconfiguration/cross_domain_screen/tokenizer-preflight-27b-probe-01.json \
  --corpus projects/distillation/wgsl/channel_gain/corpus-v1 \
  --runtime-lock projects/reconfiguration/cross_domain_screen/probe-runtime-lock-02.json

python3 projects/reconfiguration/cross_domain_screen/run_deferred_probe.py \
  --schedule projects/reconfiguration/cross_domain_screen/probe-schedule.json \
  --attempt-dir projects/reconfiguration/cross_domain_screen/probe-attempt-01 \
  --gpu-authorized
```

The second command waits without model execution for the exact self-hashed 9B
confirmation receipt: terminal confirmation status, 176 generated requests, and
the frozen runtime/stage identities in the schedule. It then waits for the
cooperative timing lock in exclusive mode. This intentionally permits the 9B
process to release its shared lock after writing its receipt. The fresh service
guard must report allowed, zero admitted stages, and an inactive/dead provider
with PID zero; it is checked again after lock acquisition and during probe work.

The wrapper holds the exclusive lock throughout the probe and passes its open
file description to the Node child. Direct probe execution requires that same
inherited, matching, exclusively locked Linux FD plus the completed receipt.
Waiting, acquisition, launch and process exit have UTC journal events. A new
attempt directory is mandatory; errors and partial outputs are retained. There
is no service control, GPU reset or automatic retry. Interruptions signal only
the wrapper's own child process group.

Exclusive admission excludes cooperating lock users. Global device isolation
remains unqualified pending live observation; neither the lock nor prior
qualification establishes isolated timing. The 593/592-token full-prefill probe
also remains separately unqualified despite the completed shorter screen.

Focused CPU checks: five Node tests passed; the two platform-independent Python
tests passed on Mac; all three Python tests passed on Jupiter, including actual
inherited-FD checks that reject absent/shared/wrong-file locks and admit an
exclusive lock. The blocking-lock fixture waited for a shared holder to release.
No GPU or model execution was part of these checks.

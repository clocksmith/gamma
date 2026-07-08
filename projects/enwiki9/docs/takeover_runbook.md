# enwiki9 Takeover Runbook

This runbook is for continuing the `enwiki9` proof pipeline without relying on
chat history. It assumes the project root is:

```text
/home/clocksmith/deco/gamma/projects/enwiki9
```

Run commands from `/home/clocksmith/deco/gamma` unless stated otherwise.

## First Checks

Generate the artifact-backed status receipt:

```bash
python3 projects/enwiki9/tools/enwiki9_status_receipt.py
```

For automation or a compact handoff, read `operator_summary` first:

```bash
python3 - <<'PY'
import json
from pathlib import Path
summary = json.loads(Path("projects/enwiki9/docs/status_receipt.json").read_text())["operator_summary"]
for key, value in summary.items():
    print(f"{key}: {value}")
PY
```

Check whether the heavy lock is held:

```bash
pgrep -af 'run_with_rss_guard|projects/enwiki9/lib/driver.py|cmix21|enwiki9-heavy.lock'
```

If a run is active:

- do not launch another compression benchmark;
- do not mutate the active candidate source;
- inspect only read-only receipts and docs;
- avoid result-corpus scans that consume scorer CPU/RAM, including
  `forecast_frontier.py` and `frontier_target_report.py`;
- continue non-heavy work from `docs/organization_audit.md`.
- check `tools/enwiki9_delayed_status_check.sh`; its
  `[unguarded_cmix_processes]` section must be `none`.
- after running `tools/enwiki9_delayed_status_check.sh`, read
  `run_logs/enwiki9_delayed_status_latest.log` for the most recent lock,
  process, RSS, temp-file, and gate-decider snapshot.

If an unguarded `cmix21-mmap-bin` process exists outside the
`run_with_rss_guard.py` process tree, stop only that orphaned process group and
preserve the locked scorer. Then remove the orphan's private temp directory and
extracted temp binary/dictionary after confirming they are not used by the
locked process.

If no run is active:

- inspect the latest result JSON for the active candidate;
- inspect its RSS guard JSON;
- update `CMIX21_LOCK_SAFE_QUEUE.md`;
- update `UPPER_BOUND_CERTIFICATE.md` only if an exact new upper-bound row is
  justified by result artifacts.

## Active Candidate Decision Tree

Current lane:

```text
cmix21_text_mmap_paq5_ppmd21120k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1
```

This candidate exists because:

- `ppmd22400k` is the best nearby archive reference;
- `ppmd22272k` passed exact `10M` replay but failed unchanged `100M` RSS by
  `36` KiB;
- `ppmd21888k` passed exact `10M` replay at archive `1,638,182`, local score
  `2,202,456`, roundtrip true, determinism true, and max sampled single RSS
  `10,482,468` KiB under the local `10,485,760` KiB guard, then failed the
  unchanged `100M` RSS guard by `36` KiB before a scored archive or roundtrip;
- `ppmd21760k` passed exact `10M` replay at archive `1,638,204`, local score
  `2,202,477`, then failed unchanged `100M` RSS by `72` KiB before a scored
  archive or roundtrip.
- `ppmd21632k` passed exact `10M` replay at archive `1,638,229`, local score
  `2,202,503`, roundtrip true, determinism true, and max sampled single RSS
  `10,482,244` KiB, then failed unchanged `100M` RSS by `68` KiB before a
  scored archive or roundtrip.
- `ppmd21504k` passed exact `10M` replay at archive `1,638,165`, local score
  `2,202,438`, then failed unchanged `100M` RSS by `72` KiB before a scored
  archive or roundtrip.
- `ppmd21376k` passed exact prefix replays but failed unchanged `100M` RSS by
  `116` KiB before a scored archive or roundtrip.
- `ppmd21248k` passed exact `1,024`, `250,000`, `1,000,000`, and
  `10,000,000` byte replays, then failed unchanged `100M` RSS by `64` KiB
  before a scored archive or roundtrip.
- `ppmd21120k` is the next PPMD-only cut. Its exact `1,024` byte replay passed
  at archive `247`, roundtrip true, determinism true, and max sampled single
  RSS `8,624,384` KiB.

Current gate:

```text
scope: 250000
mode: --check-determinism
guard: ppmd21120k_250000_determinism_rss_guard.json
```

When `ppmd21120k` finishes `250,000` byte determinism:

| Result | Action |
|---|---|
| roundtrip true, determinism true, RSS pass | record exact `250,000`; promote unchanged to the next gate. |
| archive worse but still clean | record exact penalty; decide by memory-value table before promoting. |
| RSS fail | record RSS failure; lower the smallest memory surface again. |
| roundtrip fail | mark candidate as failed at this gate; do not promote. |
| determinism fail | keep archive as non-deterministic evidence only; do not promote. |
| crash or missing JSON | record failure mode; inspect guard JSON before retrying. |

Use the decider before changing queue state:

```bash
python3 projects/enwiki9/tools/cmix21_gate_decider.py \
  cmix21_text_mmap_paq5_ppmd21120k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1 \
  --scope 250000
```

Or use the active-gate wrapper, which reads the current certificate active gate
and delegates the terminal action back to the decider:

```bash
python3 projects/enwiki9/tools/cmix21_continue_active_gate.py --refresh
```

When the wrapper reports `terminal_action_available: true`, this applies the
same decider-owned action:

```bash
python3 projects/enwiki9/tools/cmix21_continue_active_gate.py --refresh --apply-terminal
```

For a terminal pass or RSS failure, run the exact `apply_terminal_command`
printed by the decider. It records the terminal evidence and regenerates the
evidence views:

```bash
<apply_terminal_command from cmix21_gate_decider.py>
```

Do not hand-compose `--launch-next` or `--package-lower`; those flags are part
of the printed command only when the terminal verdict supports them.

If `--apply-terminal` is used when the verdict is still running, incomplete, or
a non-promotable failure state, the decider exits without executing commands.
Treat that as a queue-protection signal and inspect the printed verdict.

The decider prints one of:

```text
wait_for_gate_receipts
wait_for_rss_guard_receipt
wait_for_gate_completion
promote_unchanged
record_rss_failure_and_bracket_lower
record_roundtrip_failure
record_determinism_failure
record_guard_failure
official_accounting_audit
```

## Result Files To Read

Candidate result directory:

```text
results/<candidate_id>/
```

Expected files:

```text
<timestamp>.json
<candidate_gate>_rss_guard.json
```

For driver JSON, read:

```text
program_id
data_size
compressed_size
program_size
hutter_score
roundtrip_ok
determinism_ok or determinism
compressed_sha256
archive_sha256
error
```

For guard JSON, read:

```text
label
limit_kib
max_sampled_single_rss_kib
max_sampled_tree_rss_kib
rss_guard_exceeded
returncode
peak_sample
latest_sample
sample_count
status
```

For gates launched with the current `run_with_rss_guard.py`, the guard JSON is
also a live receipt while the command is running. Live receipts have
`status: running` and `returncode: null`. They prove monitoring is active, not
that compression has passed.

For gates launched before the live-receipt guard code was active in the running
Python process, the final guard JSON may be absent until the command exits.
Use `docs/status_receipt.md` for process-table RSS observation and keep the gate
verdict as `wait_for_gate_receipts`.

## Promotion Command Pattern

Use the lock and RSS guard for heavy gates. The exact candidate and guard path
must match the candidate being promoted.

Pattern:

```bash
flock -n /tmp/enwiki9-heavy.lock \
  python3 projects/enwiki9/tools/run_with_rss_guard.py \
    --limit-kib 10485760 \
    --sample-interval 1 \
    --guard-json <guard-json-path> \
    --label <label> \
    -- \
    python3 projects/enwiki9/lib/driver.py <candidate_id> \
      --limit <scope_bytes> \
      --check-determinism
```

Do not add archive ceilings to a promotion gate unless the purpose is explicitly
screening. A determinism/replay evidence gate needs the archive even if the
candidate is worse than expected.

## Documents To Update After A Gate

Always update:

- `CMIX21_LOCK_SAFE_QUEUE.md` with exact gate status;
- `docs/organization_audit.md` if the result changes cleanup priorities.

Record passing driver results into candidate metadata with the matching guard
receipt:

```bash
python3 projects/enwiki9/tools/record_driver_result.py <candidate_id> \
  --result <result-json-path> \
  --guard-json <rss-guard-json-path> \
  --label <gate-label> \
  --status active \
  --verdict "<exact gate verdict>"
```

Record RSS failures that have a guard receipt but no driver result with
guard-only mode:

```bash
python3 projects/enwiki9/tools/record_driver_result.py <candidate_id> \
  --guard-json <rss-guard-json-path> \
  --guard-only \
  --scope <scope-bytes> \
  --label <scope-bytes>_rss_guard_fail \
  --status active \
  --verdict "<exact RSS failure verdict>"
```

If `tools/cmix21_gate_decider.py` says
`bracket_lower_from_recorded_rss_failure`, the guard-only row is already in
`meta.json`. Skip duplicate recording and follow the lower-memory suggestion
only after the current lock is free.

Update when justified:

- `UPPER_BOUND_CERTIFICATE.md` if the gate changes best exact bounds by scope;
- `ALGORITHMS.md` if the result changes the strategy register or measured
  algorithm status;
- `CANDIDATE_INVENTORY.md` only through the inventory generator, not manual
  edits to generated facts.

After recording a terminal gate receipt, regenerate the non-heavy receipt set:

```bash
python3 projects/enwiki9/tools/enwiki9_normalize_receipts.py
```

Then rerun the decider for the just-finished scope and follow only the printed
next action.

## Claim Discipline

Allowed:

```text
passed exact 10M replay
failed 100M RSS by X KiB
first-pass archive only
roundtrip pending
determinism pending
```

Not allowed:

```text
hit 10.95
won Hutter
submission-grade
```

unless full `1G` official accounting proves it.

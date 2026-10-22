# Jupiter supplement: in progress (handoff)

Declared in [FREEZE-jupiter.md](FREEZE-jupiter.md) (commit `542187a26`) before its
targets' Mars results were seen. Mars `run-v1` is the frozen record and is committed and
verified; this run adds compute only. Handed off on 2026-10-22 while still running.

## Where it runs

- Host: Jupiter (`ssh 128`, user x).
- Checkout: fresh sparse clone `/home/x/deco-scratch/gamma-sixbit` at `542187a26`
  (not the shared `/home/x/deco/gamma`).
- Directory: `/home/x/deco-scratch/gamma-sixbit/projects/algorithm_solver/literals/sixbit-v1`
- Output: `run-jupiter-v1/` in that directory.
- Log: `/home/x/deco-scratch/sixbit-jupiter.log` (one JSON line per finished job; a
  traceback means failure).
- Interpreter: venv `/home/x/.venvs/sixbit` (Python 3.14.4, scipy 1.18.0, numpy 2.4.3).
- Process: `run_jupiter.py --output run-jupiter-v1`, PID 1985600, detached (parent init,
  own session), started 2026-10-22 10:19 EDT, with a forkserver and 4 job workers.

## Jobs and limits

| Job | Why | Limits |
| --- | --- | --- |
| `b-u-compact` | Mars phase 2 hit its 1,800 s limit without a solution | LP 7,200 s; phase 1 14,400 s; phase 2 14,400 s |
| `c-u-compact` | included before its Mars result was seen | LP 7,200 s; MILP 14,400 s |
| `a-u-canonical` | Mars LP and MILP hit their limits (unresolved) | LP 7,200 s; MILP 14,400 s |
| `a-w-canonical` | included before its Mars result was seen | LP 7,200 s; MILP 14,400 s |

Worst case is about 6 hours per A or C job and 10 hours for B, from the start time.
On Linux, `peak_rss_bytes` in the manifests is in KiB (`ru_maxrss`).

## How to tell it is done

```sh
ssh 128 'pgrep -f "run_jupiter.py --output run-jupiter-v1" || echo exited;
  cat /home/x/deco-scratch/sixbit-jupiter.log;
  ls /home/x/deco-scratch/gamma-sixbit/projects/algorithm_solver/literals/sixbit-v1/run-jupiter-v1/*/manifest.json'
```

Done means the process has exited, the log has four `{"job": ...}` lines, and all four
job directories have a `manifest.json`. A job that hit a limit still writes its manifest
(check `status` 1 and `mip_gap` in it).

## Verify, copy, commit

1. Update the scratch clone (it predates `verify_amended.py`), then verify there:

   ```sh
   cd /home/x/deco-scratch/gamma-sixbit && git pull --rebase
   cd projects/algorithm_solver/literals/sixbit-v1
   python3 -B verify_amended.py run-jupiter-v1   # writes run-jupiter-v1/verification.json
   ```

2. Bring the shared checkout to `origin/main` first. Its untracked
   `projects/algorithm_solver/literals/matched80-v3/run-v1` is tracked upstream, so a
   plain pull fails: compare it with `origin/main`, move it aside only if identical, then
   pull. Then copy and rebuild the reports:

   ```sh
   cd /home/x/deco/gamma && git fetch && git status --short
   # resolve matched80-v3/run-v1 as above, then: git pull --rebase
   D=projects/algorithm_solver/literals/sixbit-v1
   rsync -a /home/x/deco-scratch/gamma-sixbit/$D/run-jupiter-v1/ $D/run-jupiter-v1/
   cd $D
   python3 -B verify_amended.py run-jupiter-v1
   node classify_macros.mjs /home/x/deco/256one/public/labs/two-button run-v1 run-jupiter-v1
   python3 -B report.py
   ```

3. Update the verdicts in [README.md](README.md): for each job say which run it
   comes from. Keep the Mars entry as the frozen record; mark a Jupiter result as
   the compute supplement. The jobs that can change are:
   - `a-u-canonical`: resolved, or bounds tightened.
   - `b-u-compact`: selections at 64 covered programs.

   `c-u-compact` and `a-w-canonical` are replications.

4. Commit with explicit paths, then pull with rebase and push:

   ```sh
   git add $D/run-jupiter-v1 $D/macro-entries.json $D/RESULTS.md $D/README.md $D/JUPITER_HANDOFF.md
   git commit -m "Record the sixbit-v1 Jupiter compute supplement (run-jupiter-v1)"
   git pull --rebase && git push
   ```

   Mark this file complete in that commit. The scratch clone and venv can be removed
   after the push.

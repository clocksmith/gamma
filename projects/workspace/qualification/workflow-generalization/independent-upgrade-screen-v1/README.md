# Independent real-upgrade screen (v1)

**Status: protocol and screen list fixed before any run. No result yet.**

## The question

Is there one real upgrade of a real business application where an unchanged workflow still reports success and
now stores the wrong thing?

Everything the lane has measured so far used cases it wrote itself, and the five upgrades in `../three-arm-next/`
are local stand-in servers written from release notes. A guard is only worth building if the failure it guards
against exists on real software. This screen looks for one such failure. It tests no guard.

## What counts, fixed before screening

A case qualifies only if all three hold for the **same workflow**, with the same role, task and intended business
outcome:

1. it was correct before the real upgrade: on the old version it stored the right result;
2. it still reports success after the upgrade;
3. it now commits the wrong result.

Anything else does not qualify, whatever else is interesting about it. This file was committed before the screen
list and before any container was started.

**If none of the screened cases qualify, the report is "0 of N qualify", with N the exact number screened (at most
12), and the lane's paid Stage A stays parked.**

## Who does what

The screener wrote the list and the predictions and runs the screen. The screener has written none of the lane's
guards, learners or scorers, and has not read the lane's sealed files, answer keys or held-out cases.

The screener and the lane's builder work under one operator account on one machine, so this separation is a
promise and not an enforced barrier.

## Rules fixed before the first container starts

1. **The list is bounded and closed.** `screen-list.json` holds at most 12 candidates. Its SHA-256 is recorded in
   the commit that adds it, and that commit comes before any run. Nothing is added after a result is seen.
2. **Each candidate carries a written prediction:** what the old workflow will do on the new version, and the exact
   stored value expected. Predictions are scored against what happened and reported, right or wrong.
3. **Same role, same task, same intended business outcome** on the old version and the new one.
4. **The stored value is read from the database or an independent read**, never from the workflow's own success
   message.
5. **Three repeats** on fresh instances for every observation that decides a disposition.
6. **No model calls, no paid service.** Local containers only, with generated passwords, bound to the local
   machine, removed with their volumes when the case is done.

## One case, step by step

1. Bring up the old version. Set up the case. Run the old workflow. Read the stored value.
   If it is not the right value here, the case is a `setup-block`: the workflow never worked.
2. Bring up the new version with the same set-up. Run the identical steps. Record what the application reported
   (status code, message) and read the stored value.
3. On the new version, run the correct path for the same task and read the stored value, to show the task can
   still be done.

## Dispositions

| Disposition | Meaning | Counts as a qualifying failure |
| --- | --- | --- |
| `silent-wrong-write` | The old steps report success and the stored value differs from the right one, 3 of 3, and the correct path stores the right value, 3 of 3. | Yes |
| `loud-failure` | The application rejects the old steps or raises an error. | No |
| `self-healing` | The application accepts the old steps and stores the right value. | No |
| `setup-block` | The case cannot be set up, or permissions refuse the set-up. Permissions are never bypassed. | No |
| `not-run` | Not run, with the reason (for example an image that cannot be pulled). | No |

A mixed result across the three repeats is reported as mixed, with all three observations, and does not qualify.

## What gets reported

- The exact number screened and the count in each disposition, including the earlier real-software screens listed
  in `screen-list.md`, kept separate from this one.
- Each prediction beside each observation.
- If nothing qualifies: "none found among the N screened". That is not evidence that such failures are rare in
  general, and the screen is not widened to find one.
- If something qualifies: the two versions, the steps, the reported success, the stored value, the right value and
  the correct path. That case then goes to a party other than the builder, who owns it for any later comparison of
  guards.

## What this screen does not show

- Nothing about any guard, learned or hand-written.
- Nothing about cost.
- Nothing about applications or releases outside the list.

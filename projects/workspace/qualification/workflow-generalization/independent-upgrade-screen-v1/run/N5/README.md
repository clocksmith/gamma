# N5: Vikunja 0.23.0 to 0.24.0, moving a task to the Done column

One command runs the whole case and writes `../../results/N5.json`:

```sh
SCREEN_SCRATCH=/some/dir/outside/the/repository \
SCREEN_HOLD_FILE=/path/to/HOLD \
python3 run.py
```

`SCREEN_HOLD_FILE` is optional. Python 3 standard library (including `sqlite3`) and the `docker`
command are the only requirements. Passwords and the signing secret are generated per instance.

**Which install was run.** The sealed list prescribes an in-place upgrade for this case, so that the
column numbers the old workflow learned carry over. Gates B and C therefore start 0.23.0 on an empty
data volume, set the case up, stop the container and start 0.24.0 on the same volume. Gate A is a
fresh 0.23.0. A supplementary block repeats gate B on a fresh install of 0.24.0, set up through
0.24.0's own API; it is reported and does not decide the disposition.

Steps of one repeat:

1. **Bring-up**: one application container, pulled by the digest in the sealed list, with a SQLite
   file in a labelled Docker volume, on `127.0.0.1:28620` only.
2. **Set-up** through the REST API: two users register (`owner1`, `member1`); the owner creates a
   project, renames its first board column to To-Do, adds a Done column, makes Done the done column,
   creates two tasks (both start in To-Do) and gives `member1` write access.
3. **Old workflow** (gates A and B) as `member1`, as sealed: `POST /api/v1/login`, then
   `POST /api/v1/tasks/{T}` with the task's fields and `"bucket_id": D`; HTTP 200 is success. The
   body is `{"title": "Ship order 1042", "description": "", "done": false, "project_id": P,
   "bucket_id": D}` on both releases. The workflow does not read the column list first.
4. **Correct path** (gate C) as `member1`, on the second task:
   `POST /api/v1/projects/{P}/views/{V}/buckets/{D}/tasks` with `{"task_id": T2}`.
5. **Database read**: the SQLite file is copied out of the volume with `docker cp` and queried
   read-only: `tasks.bucket_id` and `tasks.done` on 0.23.0; the `task_buckets` row of the board view
   and `tasks.done` on 0.24.0. A read of the task by the owner is kept as a second witness.
6. **Tear-down**: container and volume, selected by the labels `gammatron-screen=iu1-b` and
   `iu1-b-case=N5`.

Files: `run.py` (the case), `lib.py` (helpers shared by this lane's cases).

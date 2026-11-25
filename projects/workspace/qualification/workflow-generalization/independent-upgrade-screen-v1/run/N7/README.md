# N7: NocoDB 0.107.5 to 0.108.0, a date-time written without a zone

**Status: incomplete, paused by the owner.** Gate A is recorded 3 of 3; gates B and C have no
observation. The one 0.108.0 container that was started exited with code 1 six seconds after start
(`TypeError: Cannot read properties of undefined (reading '_noco')`), before any request; this was seen
once and not diagnosed. See `../../results/N7.partial.json`.

One command runs the whole case (gates A, B and C, three repeats each, every repeat on an instance
started from nothing) and writes `../../results/N7.json`:

```sh
SCREEN_SCRATCH=/some/dir/outside/the/repository \
SCREEN_HOLD_FILE=/path/to/HOLD \
PLAYWRIGHT_MODULE=/path/to/node_modules/playwright \
python3 run.py
```

`SCREEN_HOLD_FILE` is optional. `PLAYWRIGHT_MODULE` points at an installed Playwright whose Chromium
build is present; without it the page read is recorded as not done. `--reuse` keeps repeats already
recorded in the scratch directory and runs only the missing ones. Passwords and the signing secret
are generated per instance.

Steps of one repeat:

1. **Bring-up**: one application container, pulled by the digest in the sealed list, with its SQLite
   file in a labelled Docker volume, on `127.0.0.1:28650` only. The container's time zone is the
   image default (UTC).
2. **Set-up** through the REST API: the first user signs up and owns the instance; a second user
   signs up; the owner creates a base and a table `visits` with a `When` column of type DateTime and
   adds the second user to the base as editor; the editor signs in for its `xc-auth` token.
3. **Old workflow** (gates A and B) as the editor, exactly as sealed:
   `POST /api/v1/db/data/noco/{project}/{table}` with
   `{"Title": "visit", "When": "2023-06-01 10:00:00"}`; HTTP 200 is success.
4. **Correct path** (gate C) as the editor, second row on the instance that served gate B:
   `{"Title": "visit", "When": "2023-06-01 14:00:00+00:00"}`.
5. **Three reads**, as the sealed list asks: the `when` text in the SQLite file (copied out with
   `docker cp`, opened read-only); the row as the owner's API read returns it; and what the grid
   shows the editor in a headless Chromium whose time zone is America/New_York (`page_read.cjs`).
6. **Tear-down**: container and volume, selected by the labels `gammatron-screen=iu1-b` and
   `iu1-b-case=N7`.

How the right value is applied: on 0.107.5 the SQLite text must be `2023-06-01 10:00:00`. On 0.108.0
the stored instant must be `2023-06-01T14:00:00Z`; the instant is taken from the SQLite text when
that text carries a zone, otherwise from the owner's API read. If neither carries a zone the
observation is reported as not distinguishable and the case as mixed.

Files: `run.py` (the case), `page_read.cjs` (the page read), `lib.py` (helpers shared by this lane's
cases).

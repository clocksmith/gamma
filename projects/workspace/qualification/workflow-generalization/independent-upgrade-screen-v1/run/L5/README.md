# L5: GitLab CE 15.11.13 to 16.0.0, token without expiry

**Status: nothing was run.** The work was paused by the owner before this case started. No gate was
observed and no feasibility measurement was taken; see `../../results/L5.partial.json`.

`measure.py` is a feasibility measurement only, and it has never been executed. It starts ONE
15.11.13 instance from nothing under a hard 2500 MiB memory cap (the images are amd64 only, so on
Apple Silicon they run under emulation), samples memory, state and the sign-in page every 20 s until
the instance is ready or a time bound is reached, writes what it measured to `../../results/L5.json`
and removes the instance:

```sh
SCREEN_SCRATCH=/some/dir/outside/the/repository \
SCREEN_HOLD_FILE=/path/to/HOLD \
python3 measure.py --minutes 25
```

There is no script yet for the gates themselves (project, maintainer, the old request
`POST /api/v4/projects/{P}/access_tokens`, the read of `personal_access_tokens.expires_at`).

Files: `measure.py`, `lib.py` (helpers shared by this lane's cases).

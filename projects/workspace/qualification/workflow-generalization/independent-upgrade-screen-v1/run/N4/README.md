# N4: OpenProject 15.3.0 to 15.4.0, manual scheduling becomes the default

**Status: draft, never run.** The owner paused the screen before this case started. No instance of either
release was brought up for it and nothing here has been executed; `case_meta.py` holds intended conditions,
not observed ones.

Intended use, once checked on a development instance:

```text
SCREEN_OUT_DIR=<scratch directory> SCREEN_HOLD_FILE=<hold marker file> ./run.sh
```

Two things were left to settle on a development instance before any counted repeat, and are still open:

- whether the sealed relation request, which names only `_links.to`, is accepted on 15.3.0. On 13.4.0 and
  14.0.0 (case N3) the same shape answered HTTP 500 until `_links.from` was added. `run_case.py` therefore
  records the request as sealed and, on separate work packages, the same request with `_links.from`
  (`N4_WITH_CORRECTED=0` drops the second variant);
- which of the two forms the sealed list gives for the correct path stores the right value on 15.4.0:
  creating B with `"scheduleManually": false` (`N4_CORRECT_PATH=create-automatic`, the default) or a PATCH of
  that onto B after the relation exists (`N4_CORRECT_PATH=patch-automatic`).

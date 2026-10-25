# Reviewed owned-process cleanup closure

Exact unchanged code snapshots from private reviewed freeze **06ac77aa8ec31cdb842c55ed1e5615e384eb83adc58944e57b2533e97da5c5b5**. Supported public entrypoint:

```sh
python launch_command.py --wall-seconds 900 --output NEW_PRIVATE_DIRECTORY -- EXACT_REVIEWED_COMMAND
python -m unittest -v test_supervise.py
```

`launch_command.py` imports `supervise.py`; both depend only on Python standard
library plus Linux procfs, prctl child-subreaper and pidfd facilities. Four public
Python synthetic controls exercise timeout/cancellation, detached TERM-resistant
children, rapid leader exit/adopted orphan cleanup and nonfinite deadline rejection.
No fixture evaluates JS or corpus candidates.

Dedicated supervisor only: no unrelated concurrent child creation. Its child
inventory must start empty. Absolute wall deadline includes setup; flag-only
handlers avoid asynchronous Popen assignment interruption. On stop it gives the
worker10s to finish bounded cleanup, then TERM/KILLs identity-bound owned PIDs,
including adopted detached descendants, and reaps them. Cleanup grace is up to
12s plus small observation/reap overhead and is separate from work budget. Any
unreadable ownership observation or surviving owned process fails closed.
SIGKILL/platform loss cannot have a userspace cleanup guarantee; existing native
sandbox die-with-parent remains defense in depth. No sandbox/runtime/cap edits.

**Do not invoke supervise.py as a standalone CLI.** For byte-identical provenance,
that file retains the original private Medium2 convenience entrypoint which
expects a sibling private run.py. It is not part of the supported published
entrypoint or dependency closure. Generic launch_command.py never takes that
branch. No candidate qualifier/oracle is bundled or implied by this wrapper.
Execution authorization, exact child command review, per-child limits and full
independent observation verification remain the caller's responsibility.

PROVENANCE-v1 records successful Hard3 and Medium2 observer cleanup AND separate
qualification-verifier aggregates. Supervisor process success alone is not
qualification or catalogue adoption. Earlier v1/v2 blocked preparations and review
identities remain explicit. No source bytes, packets, cases, raw stdout/stderr,
private dictionaries, binaries or credentials appear in this public snapshot.
This subtree needs a new publication allowlist; it is outside old checkpoint-v2.

# Item 44 prelaunch amendment 1: finalization failure dominance

2026-10-23 EDT. The prior activation `6a7070a9a` was not launched. Review found
that the supervisor published a successful result before cleanup, then an
unguarded log close or supervisor-receipt write could bypass failure publication.
The launch is held until this amendment and replacement pending binding receive
root and Claude review and exact-match activation.

The amended supervisor collects worker results without publishing overall success.
It then kills/reaps worker groups and closes logs under the separate ten-second
cleanup tolerance. A close failure does not skip subsequent log-close attempts within the remaining
cleanup budget; an exhausted cleanup budget stops further blocking I/O.
Success receipt and result/report publication occur only after successful cleanup,
under the remaining original 1200-second phase deadline. Cleanup does not extend
that success deadline.

Any finalization error records an incomplete outcome. Failure-receipt writes are
independent, and failure to write a receipt cannot bypass result/report withdrawal.
If replacing an artifact with incomplete metadata fails, the supervisor attempts
to remove that artifact; if failure publication itself fails, it independently
attempts removal of both public success artifacts. No implementation can guarantee
filesystem changes after the filesystem refuses both writes and removal; the
process fails and never reports completion in that case. Refused production reruns
continue to preserve the pre-existing production directory.

The new focused synthetic tests inject cleanup, log-close, receipt-writing,
partial-publication, failure-publication, and publication-timeout faults, plus a
successful completion control. Existing actual child-group cleanup tests remain
unchanged and are rerun. No private input is opened for these checks.

Scientific scope, source/pool identity, objectives, search opportunities, all
budgets, predictions, primary independent replay, and decoder charges are unchanged.
The binder additionally pins this amendment and the new test; its own changed hash
and the supervisor hash change. Offline encoder source-byte accounting changes by
the exact changed implementation sizes. The original synthetic mechanism, spec,
benchmark, tests, and recorded timings remain byte-identical. This amendment does
not authorize a run by itself; the replacement contract remains inactive until
reviewed activation.

# Item53 supplied-input complexity protocol

2026-10-24. **Harness draft only; no measurement, pin generation, scientific
freeze, private access or launch is authorized by this document.** Root has
approved implementing the isolated harness and focused invented tests. Root
reviews stable kernels and this harness, then separately authorizes preparation
of the public JSON pins and a single measurement. No existing53theorem or50file
is changed.

## Fixed inputs and comparison

Use exactly `potential-lift-certificate-v1/synthetic.py`'s two public invented
fixtures, in its existing order: paired_prefix_75k (300 strings of250 characters;
seed50065), then repeated_one_owner_12k (12 strings of1000 characters; seed50112).
Use its optional96 paid characters, bans, full shared-string pool constructor,
sorted pool order and supplied integer q rule unchanged. D=1000000, capacity256,
and all support budgets k=0,...,256 are fixed. Pool/q generation occurs only in
the later authorized timed worker, never when preparing pins. Neither fixture
contains private corpus data. No code solver, JavaScript execution, optimizer,
validation or qualification is invoked.

The public pin builder constructs only the invented strings and metadata. It
verifies50's saved spec, complete synthetic receipt, source/ban metadata and all
original code/runtime hashes, then adds an explicit list of53theorem, production,
independent checker, tests and harness files. Later scientific execution/reporting
files and README/evidence additions do not enter this measured-file inventory.
The unchanged input-spec digest is stored separately from the new harness pins.
No source, pool, q or kernel-generated result is inspected from a private path.

During the measurement require the realized source, ban, pool and q digests,
pool size/bytes, occurrence count/order, old trie-transition count, geometry,
class counts, old charge/numerator/path sum, and all257 reconstructed50rows to
match exactly the public saved50synthetic receipt. That receipt did not save top
entry identities; do not invent a historical50top digest. Instead require the
new53production and separately implemented checker to agree exactly on both
50/53 full class tops, all514 rows, all deltas, potentials/weights/new-only-top
hashes, reductions and all shared proof fields. Require exact geometry equality.
The checker uses AC/end-order paths, owner-run classification and every allowed
depth; production uses trie/backward paths and optimized unique-range aggregation.
The shared item33Index/partition/ban proof remains disclosed.

Report both complete curves, per-k charge reduction and integer-bound gain,
all input/occurrence/top/potential/weight digests, geometry, reduction counters,
production and independent work counters, and separate phase times. Store no
invented full source/q/potential/top vectors unnecessarily. Full top identity
agreement is checked before reducing those objects to hashes. A raw gain that
rounds to no integer-bound gain remains visible. No fixture/budget is selected
by its outcome.

## Timing boundary and resource contract

The single whole-run cap is180seconds from the supervisor's first monotonic
clock, before research imports/preflight. It includes public pin verification,
worker startup/imports, the3old theorem tests,7production tests and7checker tests,
fixture/pool/q construction, production reconstruction/aggregation, independent
replay, comparison, serialization, normal child cleanup/log close and final
publication. The worker inherits the same absolute deadline; no phase refresh
is allowed. Tests run before the fixture phases and their elapsed time/count
are reported separately. The first harness `import time` precedes that clock;
all later imports are included.

Item50's saved measurement ran its17small tests after the fixtures inside its
180s timer, and its harness imports preceded that timer. This new total boundary
is deliberately stricter. Compare exact inputs/results and individually labeled
phase measurements; **do not claim a strictly matched total-time ratio**, a
corpus ETA, statistical significance, or scientific certificate result from this
single supplied-input observation. No adaptive fixture shortening or retry.

Supervisor and sequential worker use core6, one native numerical thread and
8GiB RLIMIT_AS each; descendants inherit those settings. This is a per-process
address-space limit, not an aggregate8GiB cap. Report worker cumulative peakRSS
at each fixture, final worker peak and supervisor peak separately. Earlier
fixture memory contributes to later cumulative peaks; do not label them
incremental or add independent peaks as if simultaneous. Model/training costs
are zero. The inherited old pool, old occurrence graph and full substring Index
are charged in the timed worker; no full new occurrence q vector is materialized.

Use a fresh caller-supplied output directory. One worker process group is owned
by the supervisor; all descendants are killed on failure and at normal cleanup.
Normal cleanup is bounded by the original phase deadline and at most10seconds.
On failure one absolute emergency deadline is no later than first-failure+10s
and original-deadline+10s. A normal-cleanup failure uses the already-started
cleanup clock and receives no second allowance. Kill and success-marker removal
precede waits/log closes/fallible failure writes. Every operation checks/rearms
only remaining time; deadline exceptions cannot be swallowed into later I/O.
The separately supplied external190s guard is backup only, with bounded kill
cleanup. Complete acceptance still requires finishing inside180s.

The supervisor retains incomplete worker/status/log receipts, withdraws complete
results before normal cleanup, and publishes prose/supervisor receipt then final
complete results only after successful cleanup. Failure cannot convert partial
rows into a comparison. A failed receipt write may leave no final JSON; it may
never authorize acceptance. Both complete results and complete supervisor receipt
with the reviewed spec digest are required. Assertions and normal Python mode
are mandatory; `PYTHONOPTIMIZE` cannot disable invariants.

## Review and eventual commands

Before pinning, run only focused invented correctness/supervision tests. Review
actual timeout/child-death, stalled failure-write, log-close and partial-publication
paths and compare tiny supplied graphs against production/checker results.
No complexity measurement is part of those development checks.

After separate root approval, `synthetic.py --pin` prepares synthetic-spec.json
without pools/q/kernels. Root reviews and pushes those exact pins before separately
authorizing `synthetic.py --run --output <fresh-directory> --spec-sha256 <reviewed>`.
The internal --worker mode is only the supervisor's bounded child. These command
forms grant no execution authority. A later corpus experiment needs its own
input binding, FREEZE, cross-review and activation; no synthetic receipt bypasses
that gate or implies M1/coverage/semantic-reuse evidence.

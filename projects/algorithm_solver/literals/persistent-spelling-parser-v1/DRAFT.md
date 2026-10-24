# Item52: sequential persistent ban parser, supplied-input prototype

2026-10-24. Design/equivalence work only. No corpus loader, execution binder,
scientific runner, private input, benchmark or item46 modification is authorized.
Item46's failure, completion and budget remain its own evidence. This proposal
does not restart it, extend its deadline or claim ownership of item51.

## One change and unchanged authority

Replace the two fresh Node processes used by each inherited41 `banned()` call
with sequential requests to one persistent service. Keep the same two Acorn
parses: lexical ASCII validation/token/comment labels with `ecmaVersion: latest`,
then structural parsing with `latest` and the original solve-body extraction.
The lexical result is still serialized and checked against the original
32 MiB child-stdout limit, even though its labels are not returned to Python.
Do not cache sources, parser results, tries, paths or dictionaries. Do not batch
multiple logical ban calls, change the menu, or alter binding analysis: the
unchanged binding helper still uses ECMAScript2022 and eslint-scope.

The authoritative pure logic is copied into new files from
`cost-decomposition-v1/lexical.cjs` and `tail-search-v1/structure.cjs`; old helpers
remain byte-identical. Pin these authorities and Acorn/Node in a later approved
synthetic timing specification. This draft itself is not an execution freeze.

The client implements only the scalar `banned(texts)` interface. It preserves
the original insertion order and 512-item chunking of one call. Each chunk is
sent and answered before the next is sent. Whole-source strings and returned
bodies are unioned exactly as before. The transport has monotonically increasing
request IDs and checks response identity and schema. It returns no labels,
source strings in diagnostics, source executions or qualification verdicts.

## Equivalence argument and boundary

For an accepted request inside the transport limits, lexical parsing performs
the same ASCII check, token classification, comment overrides and JSON output
construction as the old child. Its UTF-8 serialized output must not exceed
33554432 bytes. Structural parsing performs the same ordered top-level walk,
function/variable declaration selection, source slices and trim operation,
including the same nonempty-body requirement. The union therefore returns
exactly the same set of strings as inherited41 `banned()`.

Induct on item46's logical encounters. With identical initial state and the same
scalar ban set or failure at each call, the unchanged engine produces the same
proposal/group order, proposal counts, scores, tie decisions, selected bytes and
ledger. In particular, it adds new variants before calling the parser and appends
the encounter only after parsing succeeds. The service must not add lookahead
variants or move these operations. Every rejected/ineligible group, duplicate
encounter, pending group and cross-arm dictionary collision remains visible.
Fresh parsing on every call means there is no cache-hit exception to this rule.

Invalid JavaScript, non-ASCII input, missing/empty solve bodies and lexical
stdout overflow all remain `subprocess.CalledProcessError` at the Python caller.
Error text, child command, stack and PID are not equivalence targets; diagnostics
use fixed enums. The client kills and attempts a bounded reap after every failure,
including transport/protocol errors and a caller's BaseException deadline. There
is no restart or automatic retry. Cleanup failure remains failure and is noted
without masking the primary exception. Outer deadline exceptions retain their class.

The prototype adds explicit transport limits: 4 MiB serialized request,
16 MiB serialized response, one outstanding request, a ten-second default request timeout
and a bounded kill/reap step. Inputs outside those limits fail closed; this is
an explicit narrower service envelope, not a claim of unrestricted equivalence
to the old CLI. The service has a 256 MiB V8 old-space ceiling and bounded input/
output buffers. This is **not** a claim that total Node RSS is256 MiB: ASTs,
token arrays, native allocations and runtime mappings are additional. No request
or source is retained between calls. Each process would inherit the existing
8 GiB address-space limit; this does not impose an aggregate memory cap. A future
adapter must measure parent/service peak RSS separately and report their combined
accounting explicitly. No cgroup or system-level resource change is proposed.

One service per anchor, on the inherited CPU affinity and process group, would
be permitted only in a future freeze. It must not detach, use uncharged cores,
outlive its anchor, or add a background pool. Its lifetime, request work, cleanup
and memory are reported under that anchor's exact existing resource contract. Tests use
short-lived supplied-input clients only. Complete untimed semantic artifacts can
be equal; deadline-driven completion counts and elapsed-time fields cannot be
promised equal after a performance change.

## Focused checks before any benchmark

Compare direct scalar bans to unchanged helpers on invented declarations,
arrows, comments, strings, duplicates, request-ID/source-key order and successive
requests. Exercise invalid syntax, non-ASCII, unsupported/empty bodies, lexical
stdout cap, transport overflow, malformed replies, service exit, timeout and
close-on-failure. A small threshold can unit-test the pure lexical byte-count
guard; that does not replace preserving its literal32 MiB production setting.

Use controlled test-only injection into inherited41 `core.banned` while calling
unchanged46 menu/apply. Compare the entire untimed menu, result, selected bytes,
trace and ledger against the old subprocess implementation. Include duplicate
renderings, numeric PID order, changed fixed dictionary order, cross-arm ban
collision, initial parse failure and failure-prefix checkpoints. Restore every
module binding after each test; never modify the active process or frozen files.

Only after root code/spec review may a separate pre-pinned synthetic timing
exercise use identical invented request sequences in both implementations.
Charge service startup, every request, output handling and cleanup; record both
semantic equality and failures. No performance number or scientific follow-up is
authorized or predicted by this draft.

Component intent is preserved: source geometry and global bans retain their
existing authority; representation/qualification decisions and all gates remain
unchanged. The only proposed mechanism is parser-process persistence.

## Completed development checks

The supplied-input prototype consists of `logic.cjs`, `service.cjs`, `client.py`
and `test_service.py`. Twelve focused tests passed in5.745 seconds with
`/home/x/deco/gamma/.venv_rocm/bin/python -m unittest -v test_service.py`.
Python compilation and Node syntax checks passed. These are correctness checks,
not a performance comparison. They include actual sequential service requests,
response data larger than a pipe chunk,512-item chunking, caller exception-class
parity, exact engine failure checkpoints, output/protocol caps, timeout and
process-group/affinity inheritance. The32 MiB lexical guard is exercised at a
small supplied threshold plus literal-limit verification; no32 MiB stress run
or throughput benchmark is claimed.

All140 frozen item46 code pins were checked unchanged. Copied authority hashes:

- `cost-decomposition-v1/lexical.cjs`:
  `44cbd5fa876ec0aebfe4d266d3b75d88fefa1e97815aa12e5d7de1f6a3eaed0f`.
- `tail-search-v1/structure.cjs`:
  `eef064a4bdc06b6c7d1c9caef2597b2fad5d3fac17e5afa99174c90d72b253d2`.

The [synthetic timing specification](TIMING-SPEC.md) and its synthetic-only harness
are awaiting final pinned-script review. Seven additional supervisor fault tests
passed using stub processes only; no timing fixture was measured. No benchmark,
scientific adapter or private-input experiment has run.

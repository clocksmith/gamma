# Known lookup v1: release gate failed

The source library and exact serving path qualify within the stated bounds.
The independent recognition candidate does **not** qualify for release.

| Evidence | Result |
|---|---:|
| Total indexed entries inventoried | 3,353 |
| Protected composition exclusions | 65 |
| Eligible exact paths executed | 3,288 |
| Approved, independently tested stored answers | 2,456 |
| Other eligible entries correctly abstained by the gated service | 832 |
| Independent known queries answered correctly | 7/20 |
| Wrong or unqualified independent acceptances | 0/24 |
| Naturally absent queries rejected | 4/4 |
| Recognition release gate | Failed: requires at least 18/20 known correct |

[Acceptance contract](../../contracts/known_lookup_release_v1.json) was frozen
before opening. The owner delegated threshold choice. This is a bounded,
agent-authored and agent-reviewed purposive sample, not human evidence. Zero
observed wrong acceptances does not imply zero true error probability. Wilson
and family-cluster intervals are retained in [summary.json](summary.json).
No result-driven threshold lowering or candidate change occurred during scoring.

## Library and exact answer path

The [source audit](../library-answer-audit-v3/README.md) executed every eligible
entry against available public and independent evidence. Approval is bound to
source bytes, provenance, corpus membership and serving code/data hashes in
[approved-library.json](approved-library.json). Exclusions are 685 missing
independent tests, 100 unqualified exact paths, 26 failed independent checks or
limits, 19 unusable imported in-place sets, two unusable independent sets, and
65 protected aliases. Missing evidence is not classified as a wrong solution.

The subsequent [gated exact-path check](exact-path-summary.json) actually called
the approved service for all 3,288 eligible entries: 2,456 returned the expected
source bytes and passed public execution; 832 abstained, with no failures.
Independent evidence was reused only for byte-identical qualified code.
The encoder never loaded on this exact path. These checks establish a bounded
source service, not reliable paraphrase identification or all-LeetCode support.

## Independent recognition and usability

[Candidate contract](contract.json) binds serving code at `4e42841a0`, data,
model, policy and sealed query bytes. The 24 initial descriptions/public examples
were the only candidate inputs; oracle signatures and private checks were kept
out. Private checks scored responses only after recording them. Correct identity
was scored separately from passing tests. The opened set is now debugging data.
The other 16 original description cases remain sealed.

Known-query warm request p50 was 293 ms and p95 380 ms, counting retrieval and
public checking. Most requests abstained; this is not accepted-answer-only speed.
[Opening](opening.json) took 302 ms to construct the context and 4.63 seconds
through encoder loading and neutral warmup, excluding Python imports. OS caches
were not flushed and the host was shared; these are not true cold-machine figures.

The real Linux service passed [desktop](editor-desktop.json) and
[mobile](editor-mobile.json) editor journeys: JavaScript and Python eight-bit
input, three public examples in each language, qualified Two Sum retrieval,
visible provenance, and explicit insertion without changing manual press counts.
The local test used an alternate loopback port to avoid another existing bridge;
only its endpoint was substituted in the test browser. This is automated
integration, not human productivity or a production deployment. Nine browser
regressions also passed, including stale responses, cancellation and focus.

## Reproduction and next candidate

The immutable provisioned-host snapshot is `/tmp/gamma-release-z9UnCT`, with
raw runs under `projects/algorithm_solver/runs/`. Durable receipt copies live
under the host workspace's ignored `runs/known-lookup-qualification-checkpoints/`.
Use the pinned source revision and catalog; current source changes deliberately
invalidate this catalog. No model or dependency downloads are required.

Next: correct empty-feature similarity rewards and compare declared interfaces
against caller-provided examples. Calibrate using development evidence, then
freeze a new candidate before opening independently authored replacement queries.
The v1 failure and its gate remain unchanged. Goal 1b is now strictly one-shot;
old clarification experiments do not define its acceptance.

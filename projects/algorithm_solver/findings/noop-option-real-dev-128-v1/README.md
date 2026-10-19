# One narrow extraction correction: real consumed-development result

The opt-in zero-action alternative correction adds one correct stored answer:
12/16 specified requests, versus 11/16 with the unchanged contradiction filter
and 7/16 with default lookup. No correct answer was lost, and no wrong acceptance,
unqualified answer or infrastructure error occurred. This is consumed development
evidence; the default route is unchanged and no release is promoted.

| Specified 16 route | Correct | Wrong accepted | Abstentions | Coverage | Full warm route p50 / p95 |
|---|---:|---:|---:|---:|---:|
| Unchanged default | 7 | 0 | 9 | 43.75% | 0.474 / 1.428s |
| Existing contradiction filter | 11 | 0 | 5 | 68.75% | 0.555 / 1.023s |
| Filter with zero-action option | 12 | 0 | 4 | 75% | 0.486 / 1.177s |

All 24-request correct/abstention counts are 7/17, 11/13 and 12/12 respectively.
The eight extra controls have no public examples and stop before retrieval;
their abstentions do not establish semantic understanding. Full warm route
maxima are 1.493s, 1.667s and 1.234s. Encoder setup was 3.499s separately, total
comparison wall 34.258s and peak sampled process-tree RSS 4,635,348,992 bytes.
The existing host workloads remained active; no exclusive-host latency claim.

## Reproduced error and correction

`stock-once` explicitly says to buy once, sell later, or do nothing. The last
option permits zero trades; it does not introduce a different transaction upper
bound. The old extractor suppressed `buy once` because its sentence contained
`or`. Consequently it could not exclude the retrieved unlimited-trades source.

`RequirementFilter(..., allow_noop_option=True)` now retains an explicit
transaction count when the sentence ends with `or do nothing`, and every `or`
belongs to that trailing option. The existing negation, conditional and quoted
context checks run first. Other alternatives remain uncertain. No fee, cooldown,
output or missing transaction count is inferred. This is a semantic rule over
explicit spans, with no problem-ID branch or score adjustment. The default
parser and policy are unchanged.

The newly selected single-trade source passed its actual approval and public
checks, then the retained source suite. Its request does not explicitly discuss
fees; this gain is correctness under the existing expected-identity/source-suite
evaluation, not proof that the full informal request has only one interpretation.
The contradiction filter remains an incomplete recognizer. The rejected
[all-abstaining required-facet candidate](../required-facets-real-dev-128-v1/README.md)
was neither expanded nor reused as this candidate.

## Per-case semantic review

[All 16 case reviews](semantic-review.json) compare full retained requests,
selected source contracts and original traces. They distinguish:

- Unsupported declaration coverage: nine selected sources have no required-facet
  contract. This alone is not evidence that the request omitted semantics.
- False suppression: `either order` for pair output, an optional zero-trade
  choice, and conditionals specifying zero/empty failure results. These do not
  automatically make the primary output or transaction count uncertain.
- Unrecognized wording: the fee case explicitly maximizes profit, but the narrow
  grammar misses its objective phrasing.
- Actual unresolved authority: no explicit fee policy in the single-trade case.
  Requiring an independent cooldown fact for a one-trade solution is excessive,
  since a post-sale restriction cannot affect another purchase when none is allowed.
- Matching failure: the rank request has all required facts and passes the gate
  but fails the frozen numeric threshold; house cases hit sibling ambiguity.
- Wrong candidate semantics: repeated trading without cooldown contradicts the
  explicit cooldown request; a bordered square differs from connected land area.

The review also records where the phrase schema cannot faithfully represent
task scope, such as measuring the supplied map without an editing operation.
Those cases are not silently labeled missing user information. Only the narrow
zero-action alternative was changed in this experiment; the other observations
remain diagnosis.

## Evidence boundary

[Frozen candidate](candidate.json), [results](summary.json),
[artifact hashes](integrity.json), [driver](compare_real.py).
Ignored raw receipts remain under `runs/noop-option-real-dev-128-v1`.
All 96 original approval-runtime bindings passed in an isolated runtime. The
original 66-entry index, 24 inputs, source approvals and thresholds were reused.
Each arm performed real query embedding/retrieval; vectors and shortlists were
identical across all three arms. Arm order alternated. All 72 decisions were
sealed before independent source-test scoring. Default control dispositions
matched history exactly, and the baseline reproduced 11 correct answers.

Focused checks: 20 tests and 62 subtests passed. No model downloads, training,
protected opening, consumed-fresh36 replay or post-score tuning occurred.

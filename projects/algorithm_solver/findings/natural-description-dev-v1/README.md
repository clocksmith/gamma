# Natural-description recognition: development baseline

Executed 2026-10-18 from an isolated current-source snapshot on host 128.
This is a Goal 1b diagnostic, not a release qualification or composition result.

## Result

The existing retrieval shortlist is useful on this authored development set:
the intended identity appears in the top five for all 16 specified descriptions.
The current selection policy is not useful for accepting them: it accepts none,
and the first-ranked candidate is wrong on six. The baseline also has no
clarification action. Its four abstentions on ambiguous descriptions do not
fulfill the requested conversational behavior.

| Input group | Cases | Correct identity first | Correct identity in first five | Accepted matches | Wrong accepted identities | Required clarifications delivered |
|---|---:|---:|---:|---:|---:|---:|
| Informal, specified descriptions | 12 | 7 | 12 | 0 | 0 | Not applicable |
| Specified descriptions with renamed signatures | 4 | 3 | 4 | 0 | 0 | Not applicable |
| Missing essential requirements | 4 | Not uniquely specified | Not uniquely specified | 0 | 0 | 0/4 |
| Out-of-domain requests | 4 | Not applicable | Not applicable | 0 | 0 | Not applicable |

All 24 requests abstained. The out-of-domain controls are weather, banking,
photo editing and email requests. They are **not genuine absent algorithm
problems**, and their rejection does not establish that harder capability.

The six incorrect first candidates are concrete selection failures even though
none crossed the existing acceptance threshold:

| Description | Intended problem | First candidate | Intended rank |
|---|---|---|---:|
| Unsorted pair, zero-based positions | Two Sum | Two Sum II | 2 |
| Houses in a straight line | House Robber | House Robber II | 2 |
| At most one stock trade | Best Time to Buy and Sell Stock | Stock II | 3 |
| Stock trading with a rest day | Stock with Cooldown | Stock II | 2 |
| Largest connected land area | Max Area of Island | Largest 1-Bordered Square | 4 |
| Kth largest value, duplicates counted | Kth Largest Element in an Array | Rank Transform of an Array | 3 |

## Timing and configuration

- AMD RYZEN AI MAX+ 395, Linux 7.0.0-38-generic, CPU inference, four Torch threads.
- Qwen3-Embedding-0.6B, hash-verified existing weights, float32, existing 3,353-entry corpus.
- Median warm embedding plus retrieval/decision: **271.9 ms**; p95: **335.6 ms**.
- Model verification/loading: **2.659 s**, reported separately. OS caches were not flushed.
- Existing frozen threshold: score >= 1.096599, margin >= 0. No threshold fitting,
  reranking, source generation, program execution or downloads.
- Specified-query top scores ranged from about 0.570 to 0.828. Merely lowering
  the threshold would not fix the six wrong first choices.

These are single serial measurements per description, not a matched performance
comparison or a claim about latency on other hardware. The host was not exclusive.
The process reported a GPU available but selected CPU explicitly.

## Evidence and reproduction

- [Dataset](../../contracts/natural_description_dev_v1.json): 24 agent-authored,
  author-reviewed development probes. Descriptions were authored without copying
  corpus statements; this does **not** make them independent human evaluation.
- [Contract](contract.json): dataset, index, source, threshold and embedding hashes.
- [Per-query receipts](recognition.jsonl): accepted decision, candidate scores,
  target identity, clarification expectation and warm elapsed time.
- [Summary](summary.json): complete denominators and grouped outcomes.
- [Runner](../../algsolve/natural_description.py) and
  [focused tests](../../tests/test_natural_description.py).

From `projects/algorithm_solver`, using the provisioned Linux environment and
existing whole-corpus files:

```sh
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 ../../.venv_rocm/bin/python -m algsolve.natural_description --name natural-description-dev-v1-reproduction --device cpu
```

Use a fresh run name; existing receipts are never overwritten. The executed
snapshot was `/tmp/gamma-natural-description-4VrCGu` on host 128. It used an
isolated copy of current source plus read-only access to existing corpus files;
the host's unrelated working-tree changes were left alone. The corpus is the
known-problem service index, not a composition training source. No protected
composition manifest, target graph, solution or test was consumed by the runner.

Before execution, the judge, lane and new diagnostic tests passed on that
snapshot: **39 tests and four subtests**, with no skips. The new six diagnostic
tests also passed locally. They check query/label separation, sibling-identity
errors despite passing answer tests, abstention versus clarification, equivalent
identities, malformed dataset rejection and reporting denominators.

## Next bounded experiment

Keep the working Goal 1a route and thresholds unchanged. Use development data
to compare requirements across shortlisted candidates: return shape/indexing,
input ordering, adjacency, trade limits and required output. Distinguish a
candidate requiring review from an accepted identity. Ask for missing essential
requirements rather than arbitrarily choosing a sibling.

Before tuning or promoting that selector, add independently reviewed natural
descriptions and genuine absent algorithm requests checked against the fixed
catalog. Review the current target annotations too. Keep a fresh protected
collection separate from this inspected development batch. Measure accepted
identity accuracy, wrong acceptance, coverage, useful clarification and complete
latency; do not promote top-five recall as successful problem identification.

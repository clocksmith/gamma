# Known lookup v2: source service verified, recognition release blocked

Frozen candidate `1abce8f5c` answered **13/20** fresh known queries correctly,
with **zero wrong acceptances**, **zero unqualified acceptances**, and **4/4
naturally absent queries rejected**. The unchanged gate requires at least 18/20
known correct: **failed, no release promotion**. [Gate](../../contracts/known_lookup_release_v2.json),
[candidate contract](contract.json), [summary](summary.json), [case outcomes](outcomes.jsonl).

The candidate was frozen before opening an independently agent-authored and
agent-reviewed replacement set. Its 20 known cases came from families absent
from the original query set; the source universe remained all 3,288 eligible
entries, without approval-based filtering. This is not human evidence. The two
independent runs use different queries; 7/20 versus 13/20 is not a matched
performance improvement estimate. The known accepted-correct Wilson interval
is 43.3–81.9%; family-cluster intervals are retained. Zero observed wrong
acceptances does not prove a zero error rate.

## What changed, and what the checks establish

- Empty extracted features no longer reward candidates for containing no evidence.
- Caller-provided public inputs and outputs reject provably incompatible declared
  interfaces. Unknown annotations and empty ambiguous containers remain inconclusive.
- Public output comparison modes are explicit, host-owned contracts: exact typed
  structure, finite ordered numeric lists with declared tolerance, distinct integer
  sets/rows, and exact rational-decimal representation. They preserve multiplicity,
  inner order and required formatting. No target-key-selected normalization occurs.
- Top-candidate public checking participates in development calibration. There is
  no search through siblings until one happens to pass. Unapproved source candidates
  remain visible; they cannot silently redirect to an approved substitute.

The development calibration accepted 194/202 old queries with no wrong identity
among public-passing acceptances. This measures threshold selection plus public
checking, **not the final catalog and sibling-guard service**, and is not fresh
qualification. Ranking-only calibration was too conservative because it counted
public-rejected programs as accepted errors; both intermediate receipts remain.

[Approved catalog](approved-library.json) still contains 2,456 independently tested
source answers. [All 3,288 eligible exact paths](exact-path-summary.json) executed
again: 2,456 approved answers, 832 abstentions, zero path failures. The encoder
never loaded. Source-independent verdicts were reused only for byte-identical code
from the completed [source audit](../library-answer-audit-v3/README.md); public
execution occurred again. These bounds do not cover arbitrary LeetCode questions.

## Failure diagnosis

| Remaining outcome | Cases |
|---|---:|
| Correct top candidate below the confidence threshold | 3 |
| Unresolved sibling distinction | 3 |
| Wrong sibling rejected by public execution | 1 |

The three low-confidence cases were Asteroid Collision, Koko Eating Bananas and
Task Scheduler. H-Index and the two Minimum Falling Path Sum variants triggered
the sibling guard. Permutations II selected Permutations; duplicate outputs failed
the declared public test. None returned an approved wrong answer. This opened set
is now debugging evidence and must not be reused as fresh qualification.

The next engineering target is requirement-aware candidate comparison on development
examples, including low similarity with a clear semantic match and explicit sibling
constraints. Retain abstention where those distinctions remain unresolved. Freeze
another candidate before any new independent opening; do not lower this gate or
claim that successful public tests alone establish problem identity.

## Runtime, latency and editor

Query embeddings use Qwen3-Embedding-0.6B through CPU PyTorch/Transformers with four
threads. Weights are the provisioned, hash-verified copy stored under Doppler's
data directory; Doppler does not execute this candidate. There is no neural
reranker or generation. The [earlier Doppler reranker configuration](../../HISTORY.md#reranker-repaired-execution-rejected-configuration)
remains rejected; it is not silently enabled.

Across all 24 warm requests, p50 was 341 ms, p95 488 ms, maximum 551 ms, including
public checking where attempted. Abstentions remain in that denominator. Context
construction took 322 ms; encoder loading plus neutral warmup reached 4.66 seconds,
excluding Python imports. [Opening receipt](opening.json). The host was shared and
OS caches were not flushed: these are not true cold-machine measurements. Bridge
workers remain disposable, so paraphrases can pay encoder startup per request.

A separate [exact-request startup receipt](exact-startup.json) measured three
fresh Python CLI processes at 484–520 ms end to end, including imports, catalog
loading and public execution. Ten retained-context exact requests took about
33 ms each; no encoder loaded. OS caches remained warm/uncontrolled. These
measurements do not describe paraphrase cold startup or whole-editor startup.

Both [desktop](editor-desktop.json) and [mobile](editor-mobile.json) passed against
the actual frozen v2 Linux service: JavaScript/Python binary input, public execution,
qualified lookup and explicit insertion. No automatic insertion or press-count
inflation occurred. The test used an isolated alternate loopback port. Production
hosting was not deployed. Thirty-three Linux judge/lane checks, 39 focused runtime
checks and seven output-contract checks passed; the counts overlap. Nine focused
browser regressions passed. No full-repository CI claim is made.

## Reproduce and preserve boundaries

[Usage](../../qualified-lookup.md) documents the approved-reference service.
The immutable provisioned-host snapshot is `/tmp/gamma-release-v2`, backed up under
`/home/x/deco/gamma/projects/algorithm_solver/runs/known-lookup-qualification-checkpoints/release-v2/`.
Its raw runs retain complete responses, independent scoring and executed examples;
expected outputs never enter candidate sandbox execution. Contracts bind source,
index, model, policy, evaluator and query hashes. No weights were downloaded.

Goal 1b shares the same engine and is strictly one description, one decision,
zero clarification questions. Its remaining 16 reserved descriptions and all
protected composition tasks remain unopened. Neither 1b nor composition is claimed
as solved by this work.

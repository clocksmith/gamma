# Gamma: Algorithm Recognition & Composition

Gamma owns the research solver, internally `algorithm_solver`; 256.one owns its
editor/interface. This descriptive title is not a separate product-name decision.

Updated 2026-10-18. Two main goals, each with two subgoals. Each subgoal
summary is 50 words, excluding its title. Composition remains unproven.
[Experiment history and reproduction details](HISTORY.md) preserve the prior handoff.

## 1. Recognize problems and retrieve stored solutions

### 1a. Recognize known problem statements

Recognize indexed problems from complete statements and paraphrases, returning qualified stored code without generation. All 3,288 eligible exact paths passed: 2,456 answers and 832 exclusions. Independent recognition failed: seven of twenty known queries answered correctly, with zero wrong acceptances. Next, repair candidate comparison and evaluate a freshly frozen replacement independently.

### 1b. Understand natural problem descriptions

Recognize indexed problems from one natural description using the same retrieval and candidate comparison engine as 1a. Return justified stored code or abstain, with zero clarification questions. Missing distinctions must not become invented constraints. Next, evaluate complete and ambiguous descriptions independently; report first-attempt correctness, wrong acceptances, coverage, and complete latency.

## 2. Learn to compose executable solutions

### 2a. Compose familiar solutions and variants

Assemble typed components into correct programs for supported problems and variants, rather than retrieving complete answers or generating source tokens. First repair malformed graph predictions and improve development training coverage. The typed student solved four of ten fitting problems and zero of eight audit problems; dependable composition remains unproven today.

### 2b. Compose unfamiliar solutions

Generalize to unfamiliar combinations of learned operations, state, bindings, and control flow through one parallel prediction and deterministic assembly. Preserve the reserved 66 problems; teacher coverage is ten, not student success. Next, diagnose development failures, finish matched search baselines, freeze all artifacts, and perform protected scoring without adapting to results.

## Matching and binary-input objectives

Goal **1b** accepts natural-language descriptions and identifies the intended
indexed problem and its requirements. Distinguish a requirement-equivalent match
from a nearby candidate, an underspecified request and an absent problem. Similarity
alone does not establish identity. Abstain when missing requirements change the answer; a twist that
requires adapting code belongs to composition, not an exact-match claim. Goal
**1a** retains complete statements and controlled paraphrases as its input scope.
Both use the same lookup engine, without generation or composition. Goal 1b is
strictly one description, one decision, zero follow-up or confirmation questions.
The earlier assisted-dialogue results remain historical development experiments.
The [one-shot contract](contracts/description_oneshot_v1.json) supersedes the
clarification provisions of the original recognition protocol for future 1b work.

The user-facing composition objective spans **2a**, then **2b**: use only `0` and
`1` to select and connect composable functions, data-structure operations, state,
control flow and recipes, with the fewest total presses to a correct solution.
Investigate a fixed-width vocabulary of **N bits, N <= 8**; eight is a candidate,
not a proven optimum. Count selection, bindings, parameters, navigation, insertion
and corrections, and report elapsed time, correctness and coverage alongside
presses. An entry selects a piece or action; a sequence builds a program. Compare
against the current seven-bit ASCII and eight-bit Python/JavaScript text-entry
baselines. Preserve those three encodings while testing a separate composable
vocabulary. Solving all LeetCode problems is the ambition, not current coverage;
encoding savings alone do not establish composition or human-effort gains.

## Evidence and operating boundaries

| Subgoal | Evidence and gap |
|---|---|
| 1a | [Source qualification and failed independent release gate](findings/known-lookup-release-v1/README.md). Exact-path success does not establish paraphrase recognition. |
| 1b | [Baseline](findings/natural-description-dev-v1/README.md): correct identity first on 10/16 specified requests, top five on 16/16; no accepted matches. [Assisted dialogue prototype](findings/clarification-dialogues-dev-v1/README.md): 20/20 scripted selections, eight abstentions, 0–3 distinction questions plus confirmation. Curated contracts and scripted confirmations are not automatic recognition or independent qualification; genuine absence and human journey time remain unmeasured. |
| 2a | [Typed student receipt](findings/typed-student-v2/summary.json): all eight audit predictions failed structural validation. [Development corpus](findings/typed-real-dev-v5/summary.json) is the permitted debugging source. |
| 2b | [Frozen reservation](contracts/typed_confirmation_v1.json) and [teacher qualification](findings/typed-confirmation-qualified-v1/summary.json). Protected student scoring has not run. |

Current recognition qualification: [complete source audit](findings/library-answer-audit-v3/README.md)
and [failed v1 recognition release](findings/known-lookup-release-v1/README.md).
The source audit accounts for all 815 historical gaps; unsupported entries are
excluded, not promoted. All 3,288 eligible requests passed the gated exact-path
check: 2,456 approved answers, 832 abstentions. Recognition v1 answered 7/20 known
queries correctly, with zero wrong acceptances and 4/4 absent rejections. The
frozen 18/20 gate failed. That opened set is now debugging evidence. A fresh
agent-authored/reviewed replacement is being prepared independently. The original
16 description cases remain sealed, with the new zero-question 1b contract.

Preserve working lookup. Keep its all-corpus index out of composition training,
mining and evaluation. Use development evidence to repair graph prediction;
protected qualification details must not feed library or training changes while
retaining an unseen claim for the same set. Unsupported cases stay in the fixed
66-problem denominator. Report recognition, composition, complete latency,
coverage and wrong acceptance separately; distinguish test agreement from problem
identity and teacher coverage from student success. The rejected reranker remains
[a reproducibility configuration](HISTORY.md#reranker-repaired-execution-rejected-configuration).

Raw data, checkpoints and per-query receipts remain in ignored `data/` and `runs/`
on host 128. [Lookup usage](HISTORY.md#use-the-answer-interface) and
[editor protocol](editor-protocol.md) retain their existing interfaces.

## Related project guidance

Owner-supplied guidance, 2026-10-18; not newly qualified by this documentation change.

- **Reploid:** Finish the ordinary conversation journey: visible search activity,
  follow-ups, reload, cancellation and authorized provider replacement. Local
  pooled-training integration already exists; its WebRTC demonstration used two
  workers on one M3, not two physical machines. Next qualify separate physical
  contributors, failures and useful adapter outcomes. Preserve consent and explicit
  activation. Whole-model service remains the default when eligible hardware fits.
- **Doppler:** Measure inference optimization and adapter training separately.
  Scratch reuse remains rejected; attribute actual execution and synchronization
  bottlenecks before another optimization. Training remains scoped to Qwen3.5
  0.8B's final down projection. Qualify broader training only when required, and
  measure complete application latency, memory, correctness and lifecycle together.
- **256.one editor:** Keep it an optional Gamma client with explicit answer
  insertion, visible provenance, public-example results and bounded execution.
  Preserve seven-bit ASCII and eight-bit JavaScript/Python contracts. Measure
  actual typing, corrections, navigation and insertion effort; verify desktop and
  mobile workflows. Encoding savings are not solver correctness improvements.

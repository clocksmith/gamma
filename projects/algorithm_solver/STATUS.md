# Gamma: Algorithm Recognition & Composition

Gamma owns the research solver, internally `algorithm_solver`; 256.one owns its
editor/interface. This descriptive title is not a separate product-name decision.

Updated 2026-10-18. Two main goals, each with two subgoals. Each subgoal
summary is 50 words, excluding its title. Composition remains unproven.
[Experiment history and reproduction details](HISTORY.md) preserve the prior handoff.

## 1. Recognize problems and retrieve stored solutions

### 1a. Recognize known problem statements

Recognize indexed problems from complete statements and paraphrases, returning qualified stored code without generation. All 3,288 eligible exact paths passed: 2,456 answers and 832 abstentions. Fresh recognition returned 13/20 correct known answers, zero wrong acceptances, and 4/4 absent rejections. The 18/20 gate failed; improve candidate comparison without lowering acceptance requirements.

### 1b. Understand natural problem descriptions

Recognize indexed problems from one natural description using the same retrieval and candidate comparison engine as 1a. Return justified stored code or abstain, with zero clarification questions. Missing distinctions must not become invented constraints. Next, evaluate complete and ambiguous descriptions independently; report first-attempt correctness, wrong acceptances, coverage, and complete latency.

## 2. Learn to compose executable solutions

### 2a. Autonomously compose known problems

Automatically assemble correct programs for known LeetCode-style problems from reusable typed graph components, without human steering or runtime source generation. Existing infrastructure solved four of ten fitting problems and zero of eight audit problems. Next, constrain graph construction, fit verified development graphs reliably, and establish an autonomous graph-development learning loop.

### 2b. Autonomously adapt nearby variants

Automatically adapt or combine learned components for nearby variants with changed constants, conditions, filtering, aggregation, or outputs. Test unseen semantic changes independently; a familiar base problem is allowed. Preserve the existing 66-problem reservation as a separate broader experiment. Measure first-attempt correctness and complete latency without human steering or runtime generation.

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

The **binary editor is a separate, optional interface experiment**, not a dependency
or acceptance gate for autonomous solving. Preserve seven-bit ASCII and eight-bit
Python/JavaScript entry. A future composable vocabulary may use N <= 8 bits per
entry; measure all selections, bindings, navigation, corrections and insertion.
Encoding savings and human effort remain distinct from solver correctness.

## Two parallel tracks with independent qualification

**Recognition (1a/1b):** improve single-shot candidate selection on development
queries, then freeze and evaluate fresh recognition cases. Retain the qualified
source catalog and failed release receipts. The 13/20 result measures recognition
only; graph-construction changes do not improve that score. Missing source tests
are a separate coverage task. No dialogue manager or weaker acceptance gate.

**Composition (2a/2b):** give the composer the problem directly. Development does
not wait for recognition to pass or require an exact stored-answer match.
Retrieving permitted reusable components is optional assistance, not problem
identification. The composition work proceeds as follows:

1. **Interface and baselines:** use the bound typed IR and the new
   [composer comparison contract](contracts/typed_composer_comparison_v1.json).
   Freeze node/edge rules, inputs/outputs, invalid-graph behavior and abstention.
   Compare raw prediction, bounded correction of that same prediction, and nearest
   frozen training graph. Preserve the old reservation's search-baseline obligations;
   reconcile any addendum explicitly before protected scoring.
2. **Development comparison:** use identical composition inputs. Preserve raw
   graphs and edit traces. Report validity, executed correctness, abstentions,
   wrong acceptances, useful/harmful corrections, construction/correction time and
   total latency. A validity-only repair is not a solved problem. Select correction
   using development cases; constraints cannot substitute a hand-authored solution.
3. **Freeze, then score:** qualify all selected routes on development data and seal
   implementations, configuration, checkpoint, encoding, components, evaluator,
   budgets and baselines. Then run one protected composition comparison. No tuning
   on its outcomes. Recognition passing is neither prerequisite nor evidence here.
4. **Separate 2b:** evaluate freshly authored nearby semantic variants under their
   own seal. Familiar bases may be allowed; changed requirements and answers remain
   unseen. Do not tune the frozen 2a composer on those variants after evaluation
   begins. Preserve the broader 66-problem reservation separately.
5. **Autonomous graph-development loop — deferred:** launch only after raw
   composition, constrained composition and protected scoring have independently
   established receipts. Then, within a recorded compute budget, propose graph
   edits, parameterizations and shared subgraphs on permitted development families;
   validate types/effects/bounds and independent oracles, repair failures and retain
   every attempt. Promote components only with contracts, tests and distinct-case
   reuse. Training on qualified graphs produces a new composer version; protected
   feedback does not become training data. Compare that later version against the
   fixed-library and parameter-only baselines on fresh frozen tasks.

Current code boundary: `typed_predictor.decisions()` independently takes argmax
for operation, child/sibling edges, bindings and types. `PredictionCodec.decode()`
then rejects invalid trees and scope/type/effect violations; it performs no repair.
The new [matched runner](algsolve/synth/compare_typed.py) adds separate raw,
bounded-correction and nearest-fit-graph routes. It retains logits, raw graphs,
edit/rejection traces, final graphs and per-phase timings, freezes public decisions
before independent scoring, and records source/dependency/input identities.
The [predeclared development configuration](contracts/typed_composer_development_v1.json)
allows one correction configuration: at most two scalar edits, 128 candidates and
0.2 seconds. Selection requires an additional correct audit answer, zero harmful
corrections/wrong acceptances, preserved fitting successes and bounded latency;
validity alone cannot qualify it. No new training campaign has started.

**Execution blocked:** the original `runs/typed-student-v2/model.pt` and
`runs/typed-real-dev-v5/pairs.jsonl` are absent locally. Host `128` is offline in
Tailscale and SSH timed out; the alternate host rejected authentication. The local
preflight fails before model execution. Focused repair/measurement tests pass,
but there is no matched development report or qualified candidate yet. Restore
the existing Linux host, run the focused judge/lane checks there, then execute:

```sh
PYTHONPATH=projects/algorithm_solver .venv/bin/python -m algsolve.synth.compare_typed --name typed-comparison-dev-v1
```

The run writes `candidate.json`, `captures.jsonl`, `decisions.jsonl`, `scores.jsonl`,
`summary.json` and `report.md` under its new run directory. A rejected candidate
remains recorded and cannot open protected scoring. Recognition remains independent.

Next checkpoint: a development-qualified frozen composer, agreed baselines and
sealed metrics, followed by one protected composition run. The existing typed IR
is frozen; matched execution, baseline qualification and the candidate seal remain
open. Neither `03e290393` nor implementation/unit tests supply a solver result.
Existing typed interpretation is sufficient; no new editor, native compiler or
replacement framework is required.

## Evidence and operating boundaries

| Subgoal | Evidence and gap |
|---|---|
| 1a | [Source qualification and failed independent release gate](findings/known-lookup-release-v2/README.md). Exact-path success does not establish paraphrase recognition. |
| 1b | [Baseline](findings/natural-description-dev-v1/README.md): correct identity first on 10/16 specified requests, top five on 16/16; no accepted matches. [Assisted dialogue prototype](findings/clarification-dialogues-dev-v1/README.md): 20/20 scripted selections, eight abstentions, 0–3 distinction questions plus confirmation. Curated contracts and scripted confirmations are not automatic recognition or independent qualification; genuine absence and human journey time remain unmeasured. |
| 2a | [Typed student receipt](findings/typed-student-v2/summary.json): all eight audit predictions failed structural validation. [Development corpus](findings/typed-real-dev-v5/summary.json) is the permitted debugging source. |
| 2b | [Frozen reservation](contracts/typed_confirmation_v1.json) and [teacher qualification](findings/typed-confirmation-qualified-v1/summary.json). Protected student scoring has not run. |

Current recognition qualification: [complete source audit](findings/library-answer-audit-v3/README.md)
and [failed v2 recognition release](findings/known-lookup-release-v2/README.md).
Both candidates completed all 3,288 gated exact paths with zero path failures.
V1 returned 7/20 known answers; fresh v2 returned 13/20. Both had zero wrong
acceptances and 4/4 absent rejections; both failed the unchanged 18/20 gate.
These are different samples, not a matched improvement estimate. Both opened sets
are now debugging evidence. The original 16 descriptions remain sealed; 1b permits
zero questions. Query embeddings currently use CPU PyTorch/Transformers; the
Doppler reranker remains rejected and disabled.

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

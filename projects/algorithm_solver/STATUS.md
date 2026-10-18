# Algorithm solver: status and handoff

Updated 2026-10-18. Two main goals, each with two subgoals. Each subgoal
summary is 50 words, excluding its title. Composition remains unproven.
[Experiment history and reproduction details](HISTORY.md) preserve the prior handoff.

## 1. Recognize problems and retrieve stored solutions

### 1a. Recognize known problem statements

Recognize indexed problems from complete statements and controlled paraphrases, return stored code, and check public examples without generation. Current evidence: 144 of 150 known queries returned independently passing answers. Next, fix sibling identification errors using development negatives and expand independent validation beyond the 2,538 currently supported stored solutions across families.

### 1b. Understand natural problem descriptions

Map informal, incomplete, conversational descriptions to the intended problem and requirements. Evaluate independently written descriptions, changed signatures, missing examples, genuine absent problems, and misleading siblings. Ask for clarification when essential details are missing. This capability is not established by controlled paraphrases. Next, create a separate development and protected evaluation collection.

## 2. Learn to compose executable solutions

### 2a. Compose familiar solutions and variants

Assemble typed components into correct programs for supported problems and variants, rather than retrieving complete answers or generating source tokens. First repair malformed graph predictions and improve development training coverage. The typed student solved four of ten fitting problems and zero of eight audit problems; dependable composition remains unproven today.

### 2b. Compose unfamiliar solutions

Generalize to unfamiliar combinations of learned operations, state, bindings, and control flow through one parallel prediction and deterministic assembly. Preserve the reserved 66 problems; teacher coverage is ten, not student success. Next, diagnose development failures, finish matched search baselines, freeze all artifacts, and perform protected scoring without adapting to results.

## Evidence and operating boundaries

| Subgoal | Evidence and gap |
|---|---|
| 1a | [Known-answer results](findings/corpus-answer-gpu-v2/) and [identity limitations](HISTORY.md#current-known-answer-qualification). Passing retrieved-problem tests does not establish the intended problem was matched. |
| 1b | No separate natural-description qualification yet; controlled paraphrases are not its acceptance evidence. |
| 2a | [Typed student receipt](findings/typed-student-v2/summary.json): all eight audit predictions failed structural validation. [Development corpus](findings/typed-real-dev-v5/summary.json) is the permitted debugging source. |
| 2b | [Frozen reservation](contracts/typed_confirmation_v1.json) and [teacher qualification](findings/typed-confirmation-qualified-v1/summary.json). Protected student scoring has not run. |

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

# CATSCAN: Request-specific reconfiguration experiments

Parent: [Gamma research projects](../CATSCAN.md)

## Target

Measure whether a fixed request-specific transform changes model behavior across
explicit task families, and distinguish useful quality changes from engineering
correctness, runtime cost and broad capability claims.

## Authority

Gamma owns task construction, independent evaluation, experimental protocols and
evidence. Doppler owns the inference runtime and transform implementation. This
component does not change the ongoing WGSL study or its frozen contract.

## Scope

Prospective multi-domain screens and studies using fixed model artifacts and
request-local transforms. The initial cross-domain screen reuses the selected
MLP channel-gain rule and existing native helper without modifying locked files.

## Contracts

- Input: owner-authorized question; pinned rule, model, runtime and task identities;
  declared controls, output limits, evaluation procedure and cost boundaries.
- Output: exact generated outputs, source locks, independent score receipts,
  paired comparisons, costs, invalid attempts and explicit claim limitations.

## Invariants

- Shared weights remain immutable; request-local state has a measured lifecycle.
- Freeze the intervention and populations before generation. Seal submitted
  outputs before reserved scoring; no outcome-based candidate tuning.
- A task must exercise transformed decode, not only the unmodified first-token
  logits of a base-cache arm. Report token counts and truncation.
- Distinguish a scored efficiency target from an actual resource or service limit.
- Preserve live services and timing validity of concurrent experiments.
- Reference implementations qualify evaluators, not model capability.

## Acceptance

Focused oracle checks accept known-correct solutions and reject plausible errors.
Every generated request has matched source/runtime identities and complete cost
accounting. Reports separate exploratory evidence from confirmatory inference and
name the measured domains, families, controls and sample counts.

## Non-goals

Reopening archived enwiki9 execution, changing production services, replacing the
running shader confirmation, tuning against reserved outcomes, or inferring broad
coding, math, writing, RSI or AGI capability from a small screen.

## Freedom

Any implementation preserving these boundaries and the frozen study contract.

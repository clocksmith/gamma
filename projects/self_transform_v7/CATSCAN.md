# CATSCAN: Self-applicable toy weight transformer

Parent: [Gamma research projects](../CATSCAN.md)

## Target

Test exact reconstruction, closure under self-target updates, and fresh-task
adaptation utility as three separate properties in a bounded CPU experiment.

## Authority

Owns this toy operator, immutable versioned child artifacts and external evaluator.
No production runtime changes; this is separate from request-local reconfiguration.

## Invariants

- Fixed external evaluator supplies only scalar losses; no held-out probe access.
- Children cannot access holdout tasks during construction or change scoring code.
- All candidates and budgets frozen before evaluation; retain losses and failures.
- Export contains all trainable state; reconstruction needs the pinned interpreter.
- No GPU use, private receipt publication, service changes, or AGI/RSI claim.

## Acceptance

`node test.mjs` verifies reconstruction, isolation, same-interface self-application,
finite-difference oracle agreement and budget accounting. `node run.mjs <path>`
verifies reconstruction in clean subprocesses and records every generation/control.

## Non-goals

A strict source-printing quine, autonomous discovery of learning signals, broad
capability, language models, or proof of sustained recursive self-improvement.

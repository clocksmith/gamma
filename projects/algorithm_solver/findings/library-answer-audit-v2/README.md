# Full-library answer qualification

2026-10-18. The metadata inventory is complete. Exact answer-path execution is
running separately; this receipt does not claim a completed answer campaign.

The [frozen protocol](../../contracts/recognition_qualification_v1.json) separates
library correctness, problem recognition and description-to-answer evaluation.
The [run contract](contract.json) freezes source, data, threshold, test and
exclusion identities. [Inventory](inventory.jsonl) records every indexed entry;
[exclusions](exclusions.json) preserve composition's reserved identities, sibling
families and transitive recorded aliases.

## Inventory

| Population | Entries |
|---|---:|
| All indexed entries | 3,353 |
| Protected entries excluded from execution | 65 |
| Eligible exact-query journeys | 3,288 |
| Historical independent-evidence gaps | 815 |
| Gaps excluded as protected | 2 |
| Eligible gaps lacking independent tests | 685 |
| Eligible gaps with available independent tests | 109 |
| Eligible gaps with unusable imported evidence | 19 |

The 19 unusable cases are in-place problems whose imported tests only assert a
`None` return, without checking the mutated input. They cannot establish the
required output. The 109 available-test gaps historically comprise 83 public
example failures, 25 independent-test runtime errors and one load error. These
are historical classifications; the current run rechecks them.

No identity, provenance-presence or interface-metadata defect was found in the
eligible inventory. That is not a claim that all programs run correctly, nor
that provenance strings alone establish source or license quality. The 815 gaps
are now accounted for, **not all resolved with passing evidence**. Missing tests
need independent oracles; unusable tests need output semantics; failures need
diagnosis against their original requirements.

## Execution and interpretation

Every eligible indexed statement and starter goes through `algsolve.answer.answer`
with its matching-interface public examples. Generation and reranking are off;
acceptance thresholds remain unchanged. Independent tests score the original
question after the answer decision. The selected stored reference is also tested
when the answer path abstains, separating library quality from recognition.

An answer counts as accepted-and-correct only when its identity matches and its
returned code passes available independent checks. Wrong identity counts as a
wrong acceptance even if available tests pass. Accepted code without independent
evidence remains unqualified. Empty/missing tests do not pass. Pre-retrieval
abstentions remain in the full-journey denominator; conditional top-five is
reported separately.

The summary includes query-type/difficulty breakdowns, rates, abstentions,
questions, p50/p95/max warm latency, Wilson intervals and family-cluster bootstrap
intervals. For the exact library census, resampling is descriptive, not sampling
uncertainty about the observed census. Neither interval accounts for weak tests.
Interim rows are an alphabetical prefix, not a representative sample of the
library; do not extrapolate their rates to the unexecuted entries. A zero-error
bootstrap interval can be degenerate, so retain the nonzero Wilson upper bound.
Cold process-to-ready includes interpreter/import time; file/OS caches are not
flushed. Independent scoring time is separate from user-facing latency.

## Reproduction and live artifacts

Host: `x@128.tail995236.ts.net`. This run uses an isolated source snapshot; the
host's unrelated dirty checkout is unchanged. No packages or model weights were
installed. Existing Qwen3-Embedding-0.6B runs on CPU with four Torch threads and
a successful compute probe.

```sh
cd /tmp/gamma-library-audit-P0ciwv/projects/algorithm_solver
/home/x/deco/gamma/.venv_rocm/bin/python -m algsolve.library_audit execute --name library-answer-audit-v2
/home/x/deco/gamma/.venv_rocm/bin/python -m algsolve.library_audit summary --name library-answer-audit-v2
```

Execution is resumable only with identical frozen inputs and source. Do not run
a second writer while tmux session `gamma-library-audit-v2` is active.
Log: `/tmp/gamma-library-audit-v2.log`. Complete raw rows, openings and progress
summaries: `runs/library-answer-audit-v2/` within that snapshot. The committed
[summary](summary.json) is a handoff snapshot at its recorded execution count,
not a live file.

A durable isolated backup (source, contract and first 268 complete result rows)
also lives at
`/home/x/deco/gamma/projects/algorithm_solver/runs/library-audit-v2-workspace/`.
Its lane is `projects/algorithm_solver/` within that directory. Prefer the newer
live receipts while the tmux run exists; this backup allows unchanged-artifact
resumption if temporary storage disappears. Do not launch both copies.

The first 72-row run is preserved in
`/tmp/gamma-library-audit-Um3nW8/projects/algorithm_solver/runs/library-answer-audit-v1/`.
It was stopped to fix cold-start timing, which originally omitted interpreter
and import time. Its partial outcomes are not merged into the corrected run.

## Verification

58 focused tests passed on Linux: judge, lane, answer, clarification and new
audit boundary tests. Seven audit tests passed again after the cold-timing fix.
Tests cover transitive protected aliases, empty evidence, incompatible interfaces,
original-query preservation, wrong identity despite passing tests, changed test
hash rejection, and uncertainty at zero successes. No full repository CI claim.

Fresh independently authored queries are sealed separately. The audit does not
open them, tune on them, alter composition, or modify the editor input alphabets.

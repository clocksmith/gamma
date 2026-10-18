# Assisted requirement clarification: development prototype

Executed 2026-10-18. This implements a dialogue over candidate requirements;
it is not a learned semantic selector or an independent Goal 1b qualification.
The existing known-answer route, thresholds, three editor encodings and protected
composition artifacts are unchanged. The browser UI does not call this CLI yet.

## Working behavior

For “Help me pick houses with the most money without choosing neighbors,” the
CLI retrieves candidates, adds explicitly curated siblings, and asks:

> These house problems differ in adjacency. How are the houses connected?

It offers a line, circle, binary tree, another requirement, or uncertainty. A
circle response narrows the curated candidates to House Robber II. The CLI then
displays the complete original statement, including examples, bounds, attribution
and license, and asks whether it matches. Only explicit confirmation accepts that
identity. This exact CLI path was exercised with scripted numeric input; its
[receipt](cli-smoke.json) is retained.

The [24 curated profiles](../../contracts/clarification_profiles_v1.json) cover
eight families and carry original-statement hashes. They were checked against
the fixed corpus by the implementing agent, not an independent reviewer. They
encode ordering/indexing, duplicates, adjacency, allowed trades/fees/waiting,
updates, grid changes and expected output where applicable. Missing facts are
not treated as false. Unknown candidates remain visible as unresolved alternatives.

The engine selects a discriminating question that minimizes the largest remaining
group, with deterministic tie breaking. It starts with five retrieved candidates
and expands only declared families, capped at 12 profiled candidates and six
distinction questions plus confirmation. Omitted candidates are disclosed.
Other, unsure, rejected statements, cancellation and exhausted budgets abstain.
Question identities prevent stale and cross-session replies; confirmation binds
to the reviewed statement hash. No code is generated, returned or executed.

The initial prose is used for retrieval only. This version does not extract
facts from it, so it can ask a question the user already answered in the original
description. Measuring and reducing that repetition is still work to do.

## Scripted development results

| Conversation group | Cases | Correct selected identity | Wrong acceptances | Abstentions | Distinction questions, median / maximum |
|---|---:|---:|---:|---:|---:|
| Specified informal descriptions | 12 | 12 | 0 | 0 | 1 / 3 |
| Descriptions with renamed signatures | 4 | 4 | 0 | 0 | 1.5 / 2 |
| Initially ambiguous descriptions, followed by scripted requirements | 4 | 4 | 0 | 0 | 1 / 2 |
| Out-of-domain controls | 4 | Not applicable | 0 | 4 | 0 / 0 |
| Variants unsupported by the curated profiles | 4 | Not applicable | 0 | 4 | 1.5 / 2 |

All 20 selections required an additional final confirmation. There were 32
distinction questions and 23 confirmation prompts across all 28 conversations.
**Three unsupported variants reached a proposed statement and were rejected only
by the scripted final “no.”** The system did not independently detect the missing
combined trading restrictions, diagonal connectivity or distinct-kth behavior.
The arbitrary-graph house request had no supported contract in its shortlist.

The [response scripts](../../contracts/clarification_dialogues_dev_v1.json) supply
requirement values, not target identities, to the dialogue. Expected identities
are passed only to scoring. Nevertheless, the same implementing agent authored
profiles and replies after examining development failures. These outcomes verify
the assisted state machine; they do not show that a model understood those
descriptions, that real users answer correctly, or that source solutions solve
the requested variants.

**Genuinely absent algorithm cases: zero.** Unsupported by these 24 profiles is
not equivalent to absent from the entire 3,353-problem corpus. Natural whole-corpus
absence remains an open acceptance requirement; easy out-of-domain requests do
not satisfy it. No protected descriptions or composition cases were opened.

## Timing

AMD RYZEN AI MAX+ 395, CPU inference with four Torch threads, existing
Qwen3-Embedding-0.6B weights, unchanged 3,353-entry retrieval corpus:

- Median complete **machine** journey: **286.4 ms**; p95 **322.9 ms**.
- Median deterministic dialogue processing, including scripted replies: **0.273 ms**.
- Model verification/loading: **2.451 s**, reported separately.
- Human reading, decisions, response time and corrections: **unmeasured**.

Each description received a fresh embedding and retrieval. Timings include
deterministic session construction, scripted answers and selection, with no
program checking. This is one serial pass on a shared host; OS caches were not
flushed. It is not a matched speedup comparison with the earlier 272 ms run.
The interactive CLI records elapsed time including user waiting, but the retained
CLI smoke used piped scripted input, not a human.

## Reproduction and checks

From `projects/algorithm_solver` in the provisioned Linux environment:

```sh
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 ../../.venv_rocm/bin/python -m algsolve.clarification_evaluation --name clarification-dialogues-dev-v1-reproduction --device cpu
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 ../../.venv_rocm/bin/python -m algsolve.clarify 'Help me pick houses with the most money without choosing neighbors.' --device cpu --receipt /tmp/house-selection.json
```

Use fresh run/receipt names. The executed isolated snapshot on host 128 was
`/tmp/gamma-clarification-vfIXHY`; the unrelated main checkout was not modified.
No dependencies, weights or datasets were downloaded. Source, dataset, profile,
index and embedding hashes are in the [contract](contract.json). Retained
[journeys](journeys.jsonl) and [summary](summary.json) expose all branches,
denominators, candidate expansion and scripted confirmations.

Before the run, **50 tests and four subtests passed**, with no skips: the judge,
lane, natural-description and clarification checks. The new 11 clarification
tests also passed locally. They cover missing requirements, unknown and omitted
candidates, question budgets, rejected statements, cancellation, stale replies,
statement binding, caller mutation and intentionally wrong scripted acceptance
remaining visible in the report.

## Remaining acceptance work

Independently review the requirement records and author fresh descriptions and
genuine absent algorithm requests against the fixed whole-corpus snapshot. Run
real users through the flow; count correct selections after clarification, wrong
acceptances, redundant questions, corrections, abstentions and complete elapsed
time. Retain “none of these” and uncertainty instead of forcing a candidate.
Review initial-description fact extraction separately before using it to skip
questions. Keep the final answer's public-example gate: selecting an identity
does not qualify a returned program.

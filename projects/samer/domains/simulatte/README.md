# Simulatte construction profile

This profile applies SAME-R to Simulatte's open-world visual construction
compiler. Gamma owns the matched outer method. Simulatte owns prompt parsing,
retrieval, construction candidates, Phase 6 compilation, Phase 7 rendering,
gold data, screenshots, adjudication, and promotion.

## Capability

The named capability is prompt-obligation-visible scene construction: the
rendered image contains the requested entities at the requested counts, in the
requested relations and poses, with recognizable silhouettes.

Embedding relevance, reranker scores, grammar IDs, scene kinds, and internal
obligation receipts are diagnostic evidence. They cannot settle the capability
claim because none of them proves what the pixels visibly depict.

## Matched lanes

| Lane | Swappable construction approach | Frozen input |
|---|---|---|
| Anchor | Category-level catalog grammar | Exact Phase 5 output |
| Targeted | Prompt-obligation coverage | Exact Phase 5 output |
| Construction control | Seeded choice from the same candidates | Exact Phase 5 output |

All lanes use the same prompt rows, candidate budget, renderer, evaluator, and
seed. The intervention is written into
`artifact.simulationCompile.renderIR.constructionApproach` before Phase 6. It
does not enter through a global, query parameter, or renderer-side prompt read.

## Gold boundary

Simulatte's first public gold set contains:

```text
5 cats in a galaxy
airplane flying over trees
3 dogs playing with 7 people
```

Each row binds expected entities, counts, relations, poses, and blocking visual
rules. The live audit binds adjudication to the exact screenshot hash. Missing
human adjudication is `not-proven`, not a machine pass.

The public rows are diagnostics and may guide development. Capability promotion
requires a family-disjoint sealed set covering animals, people, vehicles,
structures, furniture, tools, environments, and unseen composites.

## Owned artifacts

| Artifact | Owner |
|---|---|
| `tools/samer/simulatte-construction-contract.json` | Simulatte frozen trial contract |
| `tools/samer/simulatte-public-gold-v1.json` | Simulatte public gold rows |
| `tools/samer/run-construction-trial.mjs` | Simulatte matched Phase 6 executor |
| `tools/samer/gold-visual-evaluator.mjs` | Simulatte machine and human gold gate |
| `tools/audit-intent-scene-screenshots.mjs` | Simulatte live pixel collector |
| `projects/samer/experiments/experiment-register.jsonl` | Gamma immutable evidence pointers |

Run from the Simulatte repository:

```bash
npm run samer:construction:check
npm run samer:construction
npm run audit:gold:visual
```

The deterministic construction run can reach `mechanics_proven`. A visual
capability claim additionally requires matched live lane screenshots, complete
hash-bound adjudication, a sealed holdout, replication, and an immutable
experiment-register pointer.

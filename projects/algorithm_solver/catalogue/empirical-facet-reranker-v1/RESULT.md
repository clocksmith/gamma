# Fixed empirical reranker: positive coverage gain, control failure remains

Fixed0.05 adjustment changed3 top identities. Permissive correct-positive accepts rose34→37/40 while control accepts stayed9/12. At margin0.03,30→33 correct with6 controls. Zero-control coverage remains8/40. No wrong-positive acceptance was observed on this finite development cohort; that is not a risk certificate. All4081 rivals remain; raw cosine thresholds are unchanged and margins explicitly use adjusted scores. No weight sweep, model execution or confirmation.

| Policy | Correct raw→hybrid /40 | Wrong positive raw→hybrid | Controls raw→hybrid /12 | Decision changes | Hybrid Pareto |
|---|---:|---:|---:|---:|---|
| c45-m00 | 34→37 | 0→0 | 9→9 | 3 | yes |
| c45-m03 | 30→33 | 0→0 | 6→6 | 3 | yes |
| c45-m06 | 27→27 | 0→0 | 3→3 | 0 | yes |
| c45-m12 | 8→8 | 0→0 | 0→0 | 0 | yes |
| c55-m00 | 34→37 | 0→0 | 9→9 | 3 | yes |
| c55-m03 | 30→33 | 0→0 | 6→6 | 3 | yes |
| c55-m06 | 27→27 | 0→0 | 3→3 | 0 | yes |
| c55-m12 | 8→8 | 0→0 | 0→0 | 0 | yes |
| c65-m00 | 33→36 | 0→0 | 7→7 | 3 | yes |
| c65-m03 | 29→32 | 0→0 | 6→6 | 3 | no |
| c65-m06 | 27→27 | 0→0 | 3→3 | 0 | yes |
| c65-m12 | 8→8 | 0→0 | 0→0 | 0 | yes |
| c75-m00 | 27→27 | 0→0 | 4→4 | 0 | no |
| c75-m03 | 26→26 | 0→0 | 3→3 | 0 | no |
| c75-m06 | 24→24 | 0→0 | 2→2 | 0 | yes |
| c75-m12 | 8→8 | 0→0 | 0→0 | 0 | yes |
| c85-m00 | 5→5 | 0→0 | 0→0 | 0 | no |
| c85-m03 | 5→5 | 0→0 | 0→0 | 0 | no |
| c85-m06 | 5→5 | 0→0 | 0→0 | 0 | no |
| c85-m12 | 4→4 | 0→0 | 0→0 | 0 | no |

Pareto labels maximize correct positives while minimizing wrong-positive and control accepts; equivalent policies may all be nondominated. No selected-threshold-only summary hides positive-risk tradeoffs.

## Control diagnosis before any next mechanism

All12 controls generated zero tentative facets, hence the reranker leaves their scores/decisions unchanged. Six descriptions explicitly leave required choices unresolved; permissive mode accepts five. Six add custom objectives/effects that mismatch selected known contracts; permissive mode accepts four. This is not proof that every custom task is outside all4081 identities. No internally contradictory request was established. Near-neighbor resemblance cuts across both groups.

One proposed next feature is abstention on an explicitly unresolved required choice, bound to an authoritative selected-contract obligation. Failure to extract a fact alone stays UNKNOWN, never evidence that the user omitted it. Positive counterparts and adversarial scope pairs must precede any freeze; no implementation/evaluation of that proposal is claimed here.

Evidence has two separate layers: our arithmetic readback16253 recomputed all40 metric rows and exact20 baselines and checked accepted raw/adjusted gates/code pins, without ranking rerun or launch/clock attestation. Paired independent receipt94493 reproduced all non-resource result fields exactly, including rankings/decisions, under the same bounded caps; its resource timing is separate from the original run. Neither is a generalization certificate. The existing development usefulness gate and recognition qualification remain unchanged.

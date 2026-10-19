# Gamma: Algorithm Recognition & Composition

Updated 2026-10-19. All four goals remain the main research lane. Recognition and
composition qualify independently; 256.one is a separate optional interface.
[Previous full status/handoff](HISTORY-suby-20261019.md) and [experiment history](HISTORY.md)
retain earlier contracts, failures and reproduction instructions.

| Goal | Actual evidence | Next executable step / boundary |
|---|---|---|
| **1a: stored-solution recognition** | 16 reconstructed stored references qualify; full historical 1a release failed 13/20 versus unchanged 18/20 gate. The local index has 66 entries, not the historical full catalog. | Fresh sealed sample: 7/12 paraphrases and 3/8 sibling variants correct, zero wrong known-target answers. Preserve this bounded no-absence result; full-catalog gate remains unpassed. |
| **1b: one informal input, zero questions** | Frozen contradiction candidate returned 11/16 correct development answers versus 7/16 control, zero wrong/unqualified, five abstentions. Eight old no-example controls are pre-retrieval evidence only. | Fresh sample: 6/12 complete descriptions correct; only 2/4 required ambiguity abstentions, two wrong acceptances. Candidate fails required ambiguity behavior; no promotion or tuning on this opened confirmation. |
| **2a: autonomous familiar composition** | New local corpus: 24 graph labels / 18 problems qualified on 57 public + 2,975 independent cases + 24 bound probes. No-training nearest baseline returned 2/10 fit and 0/8 audit correct; 16 abstentions, zero wrong/infra. No new learned prediction result. | Prepared separate fixed CPU training runner and exact resource proposal. Freeze it before training, then freeze/execute raw versus bounded correction versus nearest graph using identical inputs and existing correctness gates. Query embedding already exceeds the two-second budget for many cases; a head-only change cannot establish latency qualification. |
| **2b: nearby semantic variants** | No independent nearby-variant result. Existing broader 66-problem reservation and protected tests remain unopened. | New separate variant-seal protocol prepared. First qualify/freeze a composer, then independently author/review changed requirements/answers; direct public input only. Do not train on or tune from opened variants. |

## Recognition evidence and next run

[Matched development result](findings/recognition-requirements-dev-suby-v1/README.md)
binds candidate `11e940fdca16abb0b968bd2459ff60285ed442f77e6c6a1bede9502296f69cfa`.
The policy, thresholds, weights, 66 entries, vectors and 16-source approval stay
unchanged. No default route or release gate was promoted.
[Fresh-query protocol](contracts/recognition_fresh_suby_v1.json) plans the existing
protocol's 12 paraphrases, eight sibling variants, 12 complete and four ambiguous
descriptions on the bounded catalog. Explicitly authorized isolated author/reviewer
agents completed and sealed
all 36 cases; seven were revised before sealing, none rejected or replaced.
[Fresh frozen result](findings/recognition-fresh-suby-v1/README.md): 16/36 correct
answers, two wrong acceptances, 18 abstentions, zero unqualified answers/questions.
Both errors were materially ambiguous descriptions, so the candidate fails the
required behavior and must not be promoted. No result-driven change was made.
Agent review is not human review; prior model exposure is unknown. The original
reserved description subset remains sealed
and is absent locally. The full-catalog 1a gate stays unpassed; this new limited
sample cannot supply its full-catalog/absence evidence. Goal 1b has no agreed
final numeric coverage threshold; do not invent one.

The completed frozen run is resumable without inference/judging while its bound
source set stays identical (93 fresh / 208 original control files preserved):

```sh
export OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 MKL_NUM_THREADS=4
export TOKENIZERS_PARALLELISM=false HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
PYTHONPATH=projects/algorithm_solver .venv/bin/python -m algsolve.fresh_recognition_suby freeze
PYTHONPATH=projects/algorithm_solver .venv/bin/python -m algsolve.fresh_recognition_suby run
```

The fresh harness passed 20 focused tests and 38 subtests before authoring. The
run counter through scoring was 34.745 seconds wall; loaded route p50/p95
0.664/1.258 seconds,
cold encoder load 4.161 seconds. All 32 known targets appeared in raw top five;
retrieval did not establish identity. A future development candidate needs explicit
negative/missing-distinction handling and separately sealed unopened confirmation.
No existing release gate or protected boundary changed.

## Composition evidence and next run

[New corpus qualification](findings/typed-lcd-suby-development-v1/README.md):
`runs/typed-lcd-suby-development-v1/pairs.jsonl` has SHA256
`6c43031ed101199ab6cdae7a8377a301988ad83d8343ad84689ccccf7e4a5cd5`.
The 15 fit / 9 audit graphs retain problem/family/pattern separation and existing
support checks. [Nearest-fit baseline](findings/typed-lcd-suby-nearest-v1/README.md)
records actual failures and complete costs.
[Existing-trace latency attribution](findings/typed-lcd-suby-latency-attribution-v1/README.md)
finds embedding/ranking alone over two seconds for 7/10 fit and 4/8 audit requests;
all 18 inputs are untruncated. Labels are existing authored teachers;
the baseline reuses fit graphs. Neither is learned autonomous solving.

[Exact training proposal](contracts/typed_lcd_suby_training_proposal_v1.json):
`typed-lcd-student-suby-v1`, 400 fixed steps, seed 17, width 64, two layers,
AdamW 0.001, four CPU threads, 8 GiB RAM, 5 GiB asset/run disk, 900-second cap,
existing frozen encoder only; no download, dependency install, protected input or
sweep. The prepared runner has not trained. AGENTS.md requires user authority for
compute jobs; the earlier scope prohibited training. Confirm that the current
broader scope authorizes this exact newly named run before launch. Do not treat
the historical `training:false` comparison contract as a new training run.

```sh
export OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 MKL_NUM_THREADS=4
export TOKENIZERS_PARALLELISM=false HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
PYTHONPATH=projects/algorithm_solver .venv/bin/python -m algsolve.synth.train_typed_suby freeze
PYTHONPATH=projects/algorithm_solver .venv/bin/python -m algsolve.synth.train_typed_suby train
```

Training loss will not be solving evidence. A new matched comparison must retain
raw predictions/logits, bounded edits, validations, public execution and complete
costs; seal all decisions before independent scoring. The unchanged two-second
warm budget and existing development correctness/latency selection remain.
[Existing comparison authority](contracts/typed_composer_comparison_v1.json) and
[correction/selection rule](contracts/typed_composer_development_v1.json) govern
those behaviors. Historical search-baseline obligations remain for the protected
campaign. No protected score or autonomous graph-development loop is authorized.
[Separate 2b protocol](contracts/nearby_variants_suby_v1.json) preserves familiar-base
permission while holding changed semantics and answers out. It declares no new
final numeric 2b coverage gate.

Historical reproduction remains blocked: original checkpoint
`25f9ca2ff223f5ae930f9511be21445efaa6dde49a697eccd5c648bdb918617c`
and corpus `566d6b440d7fdd16bac0b86114b5e8dd35ba8bd646b6bd304f8cfbc5e201330e`
are absent. New artifacts never use those identities. Development now proceeds
locally without 128; no new weights, dataset or protected data was acquired.

## Matching and binary-input objectives

1a and 1b share stored-answer recognition. Similarity, a partial requirement match
or public examples alone do not prove identity. A materially underspecified request
requires abstention; 1b permits no follow-up or confirmation question. A changed
answer belongs to composition. The binary editor is a separate optional study;
preserve seven-bit ASCII and eight-bit Python/JavaScript contracts and explicit
insertion. Encoding savings or interface tests cannot establish solver correctness.

## Operating boundary

Suby is the execution host; use its repository `.venv/bin/python` and the supported
reviewed execution context for the unchanged isolated Linux judge. Preserve
[sandbox qualification](findings/reviewed-execution-suby/summary.json), failures,
original controls, frozen vocabulary, source/test provenance and resource bounds.
Never change host security policy or use unsandboxed fallback. Keep raw source,
tests, graph labels, responses and model weights ignored and local. Commit only
code and metadata/aggregate evidence, directly to main; push and synchronize the
clean Mac Gamma checkout. No editor dependency, model auto-download, protected
opening, or claim of arbitrary unseen solving follows from these results.

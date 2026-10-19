# Gamma: Algorithm Recognition & Composition

Updated 2026-10-19. All four goals remain the main research lane. Recognition and
composition qualify independently; 256.one is a separate optional interface.
[Previous full status/handoff](HISTORY-suby-20261019.md) and [experiment history](HISTORY.md)
retain earlier contracts, failures and reproduction instructions.

| Goal | Actual evidence | Next executable step / boundary |
|---|---|---|
| **1a: stored-solution recognition** | 16 reconstructed stored references qualify; full historical 1a release failed 13/20 versus unchanged 18/20 gate. The suby reconstruction has 66 entries, not the historical full catalog. | Fresh sealed sample: 7/12 paraphrases and 3/8 sibling variants correct, zero wrong known-target answers. Preserve this bounded no-absence result; full-catalog gate remains unpassed. |
| **1b: one informal input, zero questions** | Frozen contradiction candidate returned 11/16 correct development answers versus 7/16 control, zero wrong/unqualified, five abstentions. Eight old no-example controls are pre-retrieval evidence only. | Fresh sample: 6/12 complete descriptions correct; only 2/4 required ambiguity abstentions, two wrong acceptances. Candidate fails required ambiguity behavior; no promotion or tuning on this opened confirmation. |
| **2a: autonomous familiar composition** | Original assets recovered on 128. Matched raw/corrected each returned 4/10 fit and 0/8 audit correct; nearest-fit graph 8/10 fit and 0/8 audit; zero wrong acceptances or infrastructure failures. | Correction adds no correct answer and is rejected by the frozen audit rule. Preserve original/rebuilt identities; new training still requires full-text memory qualification and owner approval. |
| **2b: nearby semantic variants** | No independent nearby-variant result. Existing broader 66-problem reservation and protected tests remain unopened. | New separate variant-seal protocol prepared. First qualify/freeze a composer, then independently author/review changed requirements/answers; direct public input only. Do not train on or tune from opened variants. |

## Recognition evidence and next run

[Matched development result](findings/recognition-requirements-dev-suby-v1/README.md)
binds candidate `11e940fdca16abb0b968bd2459ff60285ed442f77e6c6a1bede9502296f69cfa`.
That archived candidate keeps its original policy, thresholds, weights, 66 entries,
vectors and 16-source approval. A separate coordinated-negation parser patch is
software-tested but unselected; no default route or release gate was promoted.
[Fresh-query protocol](contracts/recognition_fresh_suby_v1.json) plans the existing
protocol's 12 paraphrases, eight sibling variants, 12 complete and four ambiguous
descriptions on the bounded catalog. Explicitly authorized isolated author/reviewer
agents completed and sealed
all 36 cases; seven were revised before sealing, none rejected or replaced.
[Fresh frozen result](findings/recognition-fresh-suby-v1/README.md): 16/36 correct
answers, two wrong acceptances, 18 abstentions, zero unqualified answers/questions.
Both errors were materially ambiguous descriptions, so the candidate fails the
required behavior and must not be promoted. The evaluated candidate was not
changed; follow-up code is designated separately.
Agent review is not human review; prior model exposure is unknown. The original
reserved description subset was absent on suby and remains unopened here. The full-catalog 1a gate stays unpassed; this new limited
sample cannot supply its full-catalog/absence evidence. Goal 1b has no agreed
final numeric coverage threshold; do not invent one.

The completed frozen run resumed without inference/judging (93 fresh / 208
original control files preserved). Subsequent source patches intentionally differ
from the frozen binding: these archival commands require the exact source bytes
from commit `36404d2a1`, rather than relabeling current code as that candidate:

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
[Finite post-fresh diagnosis](findings/post-fresh-diagnosis-suby-v1/README.md)
distinguishes the missing trade/duplicate semantics from a concrete coordinated
negative parser defect. The opt-in patch `recognition-negative-coordination-dev-v1`
is software-tested, unselected, with no new recognition inference. The consumed
fresh cohort was not replayed. A missing-required-facet gate is proposed, not
claimed implemented or qualified.

## Composition evidence and next run

[Recovered original matched comparison on 128](findings/reconciliation-128-v1/README.md)
completed without training. All 18 raw predictions match the historical checkpoint.
One scoring-serialization bug was fixed; the new evaluator scored byte-identical
frozen decisions under a separately recorded identity, preserving the failed run.
Raw/corrected each returned 4/10 fit and 0/8 audit accepted-correct answers; nearest
fit returned 8/10 and 0/8. All routes had zero wrong acceptances and infrastructure
failures. Correction increased fit validity by one but added no correct answer,
so the unchanged selection rule rejects it. Protected scoring remains closed.
This historical comparison retains the original 1,024-token fit-memory truncation;
it does not qualify a full-text encoding policy or the separately rebuilt corpus.

The following suby results remain distinct historical/rebuilt evidence:

[New corpus qualification](findings/typed-lcd-suby-development-v1/README.md):
`runs/typed-lcd-suby-development-v1/pairs.jsonl` has SHA256
`6c43031ed101199ab6cdae7a8377a301988ad83d8343ad84689ccccf7e4a5cd5`.
The 15 fit / 9 audit graphs retain problem/family/pattern separation and existing
support checks. [Nearest-fit baseline](findings/typed-lcd-suby-nearest-v1/README.md)
records actual failures and complete costs.
[Existing-trace latency attribution](findings/typed-lcd-suby-latency-attribution-v1/README.md)
finds embedding/ranking alone over two seconds for 7/10 fit and 4/8 audit requests;
all 18 request texts are untruncated. Labels are existing authored teachers;
the baseline reuses fit graphs. Neither is learned autonomous solving.
The follow-up audit distinguishes untruncated requests from two truncated memory
descriptions. Query vectors are already shared across matched routes; each
unique request and fit graph is encoded once. One fixed 719-token cache on/off
pair produced identical vectors but took 5.025/5.311 seconds forward-only. No
encoder, model, threshold or cap change followed; no safe two-second fix is shown.

[Exact training proposal](contracts/typed_lcd_suby_training_proposal_v1.json):
`typed-lcd-student-suby-v1`, 400 fixed steps, seed 17, width 64, two layers,
AdamW 0.001, four CPU threads, 8 GiB RAM, 5 GiB asset/run disk, 900-second cap,
existing frozen encoder only; no download, dependency install, protected input or
sweep. The prepared runner has not trained. Its new full-text preflight rejects two
fit-graph memory descriptions (1,565 and 1,660 tokens) above the existing 1,024
cap, before encoder allocation. All 18 request texts fit. The old baseline remains
intact; a separately declared full-text memory policy and new baseline identity
are needed before a valid training freeze. AGENTS.md requires user authority for
compute jobs; the earlier scope prohibited training. Confirm that the current
broader scope authorizes this exact newly named run before launch, after the
full-text encoding boundary is qualified. The commands currently refuse oversized
inputs. Do not treat the historical `training:false` comparison contract as a new training run.

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

The original checkpoint
`25f9ca2ff223f5ae930f9511be21445efaa6dde49a697eccd5c648bdb918617c`
and corpus `566d6b440d7fdd16bac0b86114b5e8dd35ba8bd646b6bd304f8cfbc5e201330e`
were recovered on 128 and verified against frozen repository contracts. Rebuilt
suby assets keep their separate identities. The full comparison and evaluator-only
recovery are retained under `runs/typed-composer-recovered-128-v1` and
`runs/typed-composer-recovered-128-scorefix-v1`. No weights or datasets were downloaded.

## Required-facet development candidate on 128

[Bounded implementation and evidence](findings/required-facets-dev-128-v1/README.md)
adds an explicit opt-in gate for missing answer-changing requirements. Ten
statement-bound stock/rank contracts are declared; unbound non-exact sources
abstain without promoting a lower candidate. Default lookup and all old receipts
remain unchanged. In 12 developer-exposed synthetic cases with fixed retrieval
and test approval, the real sandbox route retained four complete requests and
blocked eight required abstentions. Four returned programs passed eight additional
developer-authored checks. This is not retrieval qualification or a new solving
benchmark. Broad coverage loss is unmeasured; the candidate is unselected. New
training and protected composition remain gated as above.

## Real-route recognition and bounded fit repair on 128

[Real frozen-route comparison](findings/required-facets-real-dev-128-v1/README.md)
rejects the required-facet candidate for useful coverage: on 16 specified consumed
requests, unchanged control returned 7 correct answers and candidate returned 0.
Both had 0 wrong acceptances; candidate lost all 7 correct answers. Eight additional
no-example controls abstained in both arms. Actual per-arm embedding/retrieval
matched exactly; control reproduced historical dispositions. Full warm specified
route p50/p95 was 0.311/0.933 s control and 0.345/0.911 s candidate under existing host
load. No tuning or fresh qualification followed.

[Interior-slot repair replay](findings/typed-interior-empty-fit-128-v1/README.md)
adds an opt-in repair-pool eligibility fix, preserving the default. On 10 original
fit captures, validity rose 9 to10 against existing correction, but accepted-correct
answers remained 4, with 0 wrong acceptances and 6 abstentions in both arms. The
newly valid graph failed public examples. Raw predictions, original runs and all
search bounds remain intact. Repair costs were measured separately; inherited
inference makes hybrid totals unsuitable as new end-to-end latency. No audit rerun,
training, protected opening or 2a/2b qualification occurred.

## Narrow recognition gain and known-fit semantic attribution

[Three-arm real comparison](findings/noop-option-real-dev-128-v1/README.md)
measured 12/16 specified requests correct with an opt-in zero-action alternative
parser rule, versus 11/16 for unchanged contradiction filtering and 7/16 for
default lookup. No lost correct answers or observed wrong acceptances. The rule
preserves the explicit single-trade limit in “buy once … or do nothing”; it does
not infer fees or expand the rejected required-facet gate. All original controls,
thresholds and approvals remain intact. This consumed-development source-suite
gain is not proof of complete informal semantics or a release promotion.

[Known-fit diagnosis](findings/typed-fit-semantic-diagnosis-128-v1/README.md)
attributes five of six unsuccessful structurally valid cases to literal bits
only; the sixth selects stable-unique instead of sorting. Every case already has
qualified fit targets. Only 74 of 15,093 supervised literal bits are positive,
a plausible optimization issue that has not been established causally. A named
four-CPU, 8-GiB bounded literal-margin construction experiment is specified with
exact assets and acceptance criteria. Its completed result is recorded below.
No new training, target-derived solver edits, audit rerun, protected scoring or
2a/2b qualification occurred.

## Literal-margin fit experiment on 128

[The frozen bounded candidate](findings/typed-literal-margin-fit-128-v1/README.md)
returned 2/10 accepted-correct answers, matching its structural control; nearest
training graph returned 4/10. Every arm had zero wrong acceptances and zero
infrastructure failures. Candidate p95 was 5.134 seconds against the unchanged
two-second warm budget, so acceptance failed. All ten raw predictions matched
historical captures exactly. Only one additional literal public execution was
possible and it timed out; the five previously diagnosed literal-only cases
never reached repair because inference exhausted the decision budget. This is
limited mechanism evidence, not proof that literal repair cannot help. The raw
logits, decisions, repair traces and independent scores are preserved and sealed.
No post-score tuning, budget relaxation, training, protected opening or default
route promotion followed. Software checks passed separately: 50 tests plus
5 subtests, then 5 repair tests plus 2 subtests after final overhead accounting.

## Timing reconciliation and measured wait overhead

[Exact loss attribution](findings/typed-timing-reconciliation-128-v1/README.md)
reconciles structural 4/10 to 2/10 and nearest 8/10 to 4/10: all six arm-level
losses retain identical correct source and occur because fresh embedding alone
exceeded two seconds, before any public sandbox execution. Cold encoder setup is
outside the warm gate; warm embedding and complete sandbox overhead are inside.
A current paired placement probe did not reproduce the historical slowdown or
justify an affinity change. Historical contention is not causally identified.
A reproduced Python process-wait delay was removed with a host pidfd notification,
preserving all isolation, limits and cleanup; synthetic median judge time fell
32.155 to 24.791 ms. This does not change solver scores. All 54 focused tests and
5 subtests passed. Post-score label analysis places two known literal repairs at
proposal ranks 1 and 3, so training is not yet the demonstrated immediate need.
The rejected candidate, two-second gate and all training/protected boundaries
remain intact; stabilize and instrument execution before a new quality pass.

## Matching and binary-input objectives

1a and 1b share stored-answer recognition. Similarity, a partial requirement match
or public examples alone do not prove identity. A materially underspecified request
requires abstention; 1b permits no follow-up or confirmation question. A changed
answer belongs to composition. The binary editor is a separate optional study;
preserve seven-bit ASCII and eight-bit Python/JavaScript contracts and explicit
insertion. Encoding savings or interface tests cannot establish solver correctness.

## Operating boundary

128 is the execution host; use its repository `.venv_rocm/bin/python` (the default
`.venv` lacks PyTorch) and normal reviewed execution for the isolated Linux judge.
The current host passed 78 focused tests plus 58 subtests; the scoring fix passed
23 focused tests plus 11 subtests. Those overlapping software checks are separate
from solving evidence. All six existing SSH directions among 128, suby and macOS
passed strict pinned host-key checks. Preserve
[sandbox qualification](findings/reviewed-execution-suby/summary.json), failures,
original controls, frozen vocabulary, source/test provenance and resource bounds.
Never change host security policy or use unsandboxed fallback. Keep raw source,
tests, graph labels, responses and model weights ignored and local. Commit only
code and metadata/aggregate evidence, directly to main; push and synchronize the
clean Mac Gamma checkout. No editor dependency, model auto-download, protected
opening, or claim of arbitrary unseen solving follows from these results.

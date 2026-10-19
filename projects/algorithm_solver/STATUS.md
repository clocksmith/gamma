# Gamma: Algorithm Recognition & Composition

Gamma owns the research solver, internally `algorithm_solver`; 256.one owns its
editor/interface. This descriptive title is not a separate product-name decision.

Updated 2026-10-19. Two main goals, each with two subgoals. Each subgoal
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

**Execution handoff:** suby is the primary execution computer, using
`ssh -o HostKeyAlias=suby.tail995236.ts.net clocksmith@192.168.86.54` and
`/home/clocksmith/deco/gamma`. Read its applicable instructions before work.
The original `runs/typed-student-v2/model.pt` and
`runs/typed-real-dev-v5/pairs.jsonl` are absent on both the Mac and suby.
Host `128` and recovery after reboot remain unverified. Recover the original
hash-matching assets; do not silently retrain or substitute another corpus.

[Historical suby software checks](findings/comparison-software-checks-suby/summary.json)
at `47625acce` had 49 passing tests, 18 failures and 43 passing subtests; retain
both earlier logs and the AppArmor startup-denial evidence. A later ordinary
restricted task context also denied socket creation. Neither established that
command-specific reviewed execution was unavailable.

**Current judge qualification:** the supported reviewed execution path now passes
one harmless startup probe and **62 focused tests plus 19 subtests**, with zero
failures, skips or deselections, in 10.88 seconds. These include actual sandbox
execution and existing network/filesystem/process/resource containment checks.
[Reviewed qualification receipt and raw logs](findings/reviewed-execution-suby/summary.json)
bind the source, context, command and results. The existing bubblewrap isolation
was unchanged; no host security setting, key or credential was modified. Original
model/corpus assets remain missing. After restoring and hash-verifying them, use
the approved reviewed context for the existing development comparison:

```sh
PYTHONPATH=projects/algorithm_solver .venv/bin/python -m algsolve.synth.compare_typed --name typed-comparison-dev-v1
```

The run writes `candidate.json`, `captures.jsonl`, `decisions.jsonl`, `scores.jsonl`,
`summary.json` and `report.md` under its new run directory. A rejected candidate
remains recorded and cannot open protected scoring. Each scored route is saved
atomically under `scoring/`; resume only missing scores with the same `--name`
and `--resume-scoring`. Candidate, decision, cohort or test-identity drift blocks
resumption. Incomplete scores cannot produce a report. Recognition remains
independent; no matched model report or development-qualified candidate exists yet.

Next checkpoint: a development-qualified frozen composer, agreed baselines and
sealed metrics, followed by one protected composition run. The existing typed IR
is frozen; matched execution, baseline qualification and the candidate seal remain
open. Neither `03e290393` nor implementation/unit tests supply a solver result.
Existing typed interpretation is sufficient; no new editor, native compiler or
replacement framework is required.

## Suby development inspection, 2026-10-19

Recognition development proceeded independently of blocked composition execution.
A synthetic caller-public-data probe found that candidate return-type filtering
handled `return` but skipped the runner's default `return:exact`. The filter now
checks that exact mode too, preserving exact judging's lossless integer/float
equivalence without changing caller examples or relaxing input types. Non-exact
comparison modes remain inconclusive at this filter. This fixes an interface
boundary; passing software checks does not establish recognition or learned
solving improvement. The source-bound approved catalog must be requalified for
this changed runtime before new serving or evaluation claims; retain old catalog
and raw receipts unchanged. No threshold or acceptance requirement changed.

Validation on suby: 36 tests and seven subtests passed, one real-sandbox test
deselected, using the command below. Touched-file compilation and module import
also passed. These are software checks, not the earlier 49-pass/18-failure
qualification campaign and not new corpus or protected evaluation evidence.

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=projects/algorithm_solver:projects/algorithm_solver/tests .venv/bin/python -m pytest -q -p no:cacheprovider projects/algorithm_solver/tests/test_interface_compatibility.py projects/algorithm_solver/tests/test_approved_library.py projects/algorithm_solver/tests/test_declared_comparison.py tests/test_algorithm_solver_lane.py -k 'not test_declared_public_contract_survives_both_editor_execution_paths'
```

Remaining gaps and next actions:

- Local `data/` is absent, including the recognition catalog and embeddings;
  original composition checkpoint and qualified corpus remain absent too.
  Recover original source-bound assets only through verified, authorized access;
  do not substitute rebuilt assets under their identities.
- SSH to both configured aliases and the supplied 128 LAN address fails at
  local socket creation (`Operation not permitted`), before any handshake.
  This establishes neither remote identity nor that 128 is offline.
- The owner independently reverified Mac's live ED25519 fingerprint as
  `SHA256:CvRB17NZ4kZcZFmCYQV75lz7f/q8b24KqCJOzlYO/cU`, matching the
  already-stored key, and reports strict suby-to-Mac SSH succeeded outside this
  restricted task. This supersedes the earlier `ZcBG...` inventory value;
  the fingerprint discrepancy is resolved. No trust rewrite is needed.
  This task did not retry SSH or execute the authorization script, and its local
  socket restriction remains distinct from the owner's successful connection.
- The current bubblewrap probe fails before payload execution at
  `Failed to create NETLINK_ROUTE socket: Operation not permitted`.
  The enclosing Codex process already inherits one seccomp filter,
  `NoNewPrivs=1` and zero capabilities. Syscall tracing is denied too.
  No readable seccomp denial record identifies the exact filter rule; do not
  attribute this current socket failure solely to AppArmor.
- Separately, the kernel journal records earlier AppArmor denials of `net_admin`
  and `setpcap` for bubblewrap under `unprivileged_userns` on 2026-10-18.
  A platform-approved execution session on suby must permit the needed SSH
  sockets and nested bubblewrap setup while preserving the existing isolation
  contract. An inherited filter cannot be removed by a child process. If host
  AppArmor still denies the approved session, an administrator must supply an
  approved judge execution profile. No host policy change or bypass is authorized
  by this work; no unsandboxed fallback is permitted.
- After access, original assets and isolation are qualified, rerun the judge and
  lane acceptance checks, then the declared development comparison command above
  in the composition section. Historical search baselines and an explicit seal
  remain required before protected composition scoring. For recognition, freeze
  and requalify the changed runtime on permitted development assets before any
  fresh independent evaluation. No sealed description cases were opened;
  Goal 1b still permits one initial request and zero questions.

## Further permitted software development, 2026-10-19

Continued from the clean, owner-synchronized merge `960c485ac` without accessing
128 or retrying denied network/sandbox operations. The recognition boundary now
refuses malformed public-example subsets: unmatched explicit `Input` blocks are
counted as dropped, and conversion/arithmetic failures in the restricted value
parser become `Unsupported` data rather than uncaught host exceptions. A valid
example followed by an unfinished or invalid example now produces one-shot
abstention before lookup or judging. The parser still executes only its existing
whitelist; no new expression forms, questions, thresholds or acceptance rules
were added. Existing corpus bytes and qualification receipts remain untouched.

A separate composition scoring defect was reproduced with a synthetic callback:
mutating one route's expected value changed subsequent routes' expectations from
3 to 4 to 5. The scorer now owns a detached test snapshot, passes each route its
own copy and verifies its test hash again before publishing a verdict. Mutation
fails closed before that receipt is written; prior receipts survive and normal
resumption uses the same sealed tests. This preserves the matched-evidence
boundary without changing the frozen vocabulary or original asset identities.

Validation: **56 tests and 26 subtests passed in 0.43 seconds**, one real-sandbox
comparison test deliberately deselected. All five touched Python files compiled
and all changed modules imported. These synthetic fixtures and mocked verdicts
are software checks only, not isolated-execution evidence, recognition accuracy
or learned solving improvement. The earlier blocked judge campaign remains open.
[Source-bound software receipt](findings/development-software-boundaries-suby/summary.json)
records the exact command, source hashes, reproductions and remaining gates.

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=projects/algorithm_solver:projects/algorithm_solver/tests .venv/bin/python -m pytest -q -p no:cacheprovider projects/algorithm_solver/tests/test_public_examples.py tests/test_algorithm_solver_lane.py projects/algorithm_solver/tests/test_interface_compatibility.py projects/algorithm_solver/tests/test_approved_library.py projects/algorithm_solver/tests/test_typed_scoring.py projects/algorithm_solver/tests/test_typed_comparison.py -k 'not test_real_sandbox_distinguishes_invalid_repaired_and_valid_wrong'
```

Next measurable recognition work requires the original development catalog,
corpus embeddings and source-bound approval inputs, followed by an approved
isolated judge and requalification of the changed serving runtime. Until those
inputs are available, no catalog-level accuracy claim is supported. The original
checkpoint/corpus matched composition run and its search-baseline obligations
remain blocked as above. Do not replace missing originals, reopen protected
cases, or treat this software validation as permission to freeze a composer.
Component intent is preserved; authority and lane boundaries are unchanged.

## Goal completion gates and local prerequisites, 2026-10-19

A read-only audit at `bccbf685e` found no permitted local experiment that can
currently demonstrate another accepted correct answer. The historical approval
manifest and authored description development receipts are retained, but the
serving corpus, stored-code inputs, vectors, source tests and original composition
assets are absent. The configured Qwen encoder directory is absent too. The local
Doppler embedding directory contains only a tokenizer and manifest: **zero of
nine weight shards are present**. It is not a provisioned substitute encoder.
[Readiness receipt](findings/goal-readiness-suby/summary.json) binds the governing
contracts, exact missing paths, original hashes and the minimum unblock per goal.

| Goal | Existing gate and result | Next measurable step and minimum prerequisite |
|---|---|---|
| 1a | At least 18/20 correct known answers; zero wrong/unqualified acceptances; 4/4 absent rejections. Historical v2 reached 13/20 and failed. | Restore the permitted source/index/test bundle and approved isolated judge; requalify actual exact answer paths. Exact lookup needs no encoder load. Paraphrase development additionally needs the frozen Qwen encoder. |
| 1b | Correct identity plus qualified executed stored code, one initial description, zero questions and abstention on unresolved requirements. No numeric final coverage threshold is declared. | Same assets and judge as 1a; measure first-attempt returned-correct development answers. Before future confirmation, agree a numeric coverage/correctness criterion while preserving the existing evidence and zero-question rules. |
| 2a | The next gate requires at least one additional correct audit answer, zero harm/wrong acceptance/infrastructure failure, preserved fit successes, and the declared latency bounds. It is a development-selection gate, not goal completion. | Restore original checkpoint/pairs, corresponding development test files and Qwen encoder; qualify isolation; run the matched development comparison. Historical search baselines and a complete seal remain required afterward. |
| 2b | Separately sealed fresh semantic variants with unseen changed answers; first-attempt correctness and complete latency; no post-opening tuning. The existing 66-problem reservation stays separate. No numeric final variant threshold is declared. | First qualify a composer through 2a development, then agree and seal the separate variant criterion/cohort before a later authorized opening. No variants are opened in this turn. |

The smallest common user action is to provision those original permitted assets
from an accessible backup or local source and provide an approved suby execution
session supporting the existing isolated judge. That does not require contacting
128 if a backup exists. No child-side code change can remove inherited platform
restrictions, and no such bypass or host-security change is authorized.

If original composition assets cannot be recovered, the receipt proposes—but does
not initiate—a separately named `typed-student-suby-development-v1`: newly
identified/qualified development data, existing IR, four CPU threads and one fixed
400-step training configuration. It requires explicit owner approval, provisioned
encoder and an approved judge. It cannot be called the original experiment or
replace its assets. No new numerical qualification, tests, downloads or model
runs occurred in this audit. No candidate is eligible for confirmation yet.
Further code-only fixture work would not close any of these evidence gaps;
there is no supported completion percentage to report.

## Reviewed execution update, 2026-10-19

The previous readiness audit describes the ordinary restricted task context.
Command-specific automatic approval review subsequently permitted strict Mac SSH,
Git fetch/push and the unchanged Linux judge qualification. Under that supported
path the suby process reports `Seccomp: 0` and `NoNewPrivs: 0`, while the host
AppArmor user-namespace restriction remains enabled. The probe and all focused
qualification tests passed. This resolves the tested judge-startup boundary in
reviewed execution; ordinary task socket restrictions are not an outstanding
reason to reject that approved path. Historical failures remain preserved.

Strict SSH returned `mac.lan` / `xyz`. The Mac's existing stored host key was
retained. Metadata-only workspace/back-up searches found neither the recognition
source/index bundle nor the original composition checkpoint/corpus. No protected
contents or private credentials were read; 128 was not contacted. Other local
embedding models are not approved substitutes and were not loaded.

Commits `bccbf685e` and `5b83b24f8` were normally pushed to `origin/main`, and the
clean Mac Gamma checkout fast-forwarded to `5b83b24f8`. Its wrapper lacked Node in
the noninteractive PATH; existing Git performed the guarded fast-forward without
installing anything. Only Gamma was synchronized.

The smallest remaining common unblock is now **the original permitted development
asset bundle and frozen encoder**, supplied from any authorized accessible backup
or local source. The focused isolated-judge prerequisite is satisfied in reviewed
execution. No new download, training run, replacement experiment or protected
opening is authorized by this result. No model accuracy or learned-solving result
exists, and no candidate is eligible for confirmation. Continue the declared
development gates only after the missing inputs pass their original hash checks.

## Approved recognition reconstruction completed, 2026-10-19

The recognition asset blocker is resolved for a **new bounded LCD-only development
pilot**, not for reproduction of the historical complete service. The owner
approved only the pinned encoder and LCD training file: 1,296,663,981 bytes were
downloaded and hash-verified. Protected identity/family/recorded-alias exclusions
were applied before indexing or qualification; historical files and thresholds
were not changed. The frozen 83-key development shortlist yielded 66 available
permitted entries, including all 16 requested targets.

[Reconstruction finding](findings/recognition-rebuild-dev-suby-v1/README.md) and
[aggregate receipt](findings/recognition-rebuild-dev-suby-v1/summary.json): all
16 stored target references passed 39 public cases, 1,418 imported independent
cases and their actual exact-answer paths. The one-shot description pilot
returned **7/16 specified answers correctly**, zero wrong or unqualified answers,
and nine abstentions. All 24 requests remain in the denominator; four ambiguous
and four out-of-domain controls abstained at the missing-public-example gate.
Those eight results are not evidence of semantic ambiguity or absence detection.
No questions were asked. Fixtures add target-source public examples to the old
authored descriptions; no oracle signature or target identity enters the route.
This is not matched improvement over the old description-only baseline.

Specified warm route p50/p95 was **0.777/0.937 seconds**. The pilot completed in
240.05 seconds wall time, with 3.98 GB observed peak aggregate RSS and 1.30 GB
monitored disk, within the approved four-thread / 8 GiB RAM / 5 GiB disk envelope.
Completed-run resumption preserved 208 artifact contents and mtimes without new
inference or judging. Raw source data, weights, test payloads and code-bearing
responses stay local and ignored. Only aggregate evidence and runner code are
committed; the license discrepancy and source attribution are retained.

Next meaningful development work is a separately sealed requirement-aware
candidate comparison against this fixed control, preserving the nine abstentions
and recording matched costs. Do not tune or overwrite this completed candidate,
claim fresh confirmation, lower acceptance gates or start composer training.
The historical 3,353-entry reproduction and original matched composition run
remain unavailable; protected evaluation remains unopened.

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

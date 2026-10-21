# Gamma Goals

## Mission & Thesis

Gamma delivers an empirical workbench and research laboratory for machine learning model evaluation, distillation, multi-backend comparison, and capability-transfer research.

**Model behavior is verifiable science, not opaque intuition.**

Evaluating and transferring capabilities across compact language models, translation systems, and algorithmic reasoning engines requires strict experimental controls. Gamma makes token prediction, distillation pipelines, and hardware execution head-to-head comparable by anchoring every trial to an explicit run contract, frozen evaluation datasets, and reproducible scoreboards.

## Intended Beneficiaries

1. **Model Optimization & Distillation Researchers**: Engineers creating compact student models (e.g., `TranslateGemma-4B -> Gemma-3-1B`) who require verified translation loss, latency, and parameter audits.
2. **Evaluation & Benchmark Analysts**: Teams comparing model families across heterogeneous backends (ROCm, CUDA, WebGPU) with tamper-proof scorecards.
3. **Autonomous Agent Systems (Reploid)**: Upstream consumers utilizing SAME-R capability transfer and empirical validation matrices to guide model selection.

## Desired Outcomes

1. **Named Run Contracts**: Every evaluation and training execution binds to an explicit `[run-contract]` capturing dataset, schedule, hyperparameters, and device identity.
2. **Decoupled Reporting**: Rebuilding reports, manifests, and scoreboards operates strictly asynchronously and cannot corrupt or deadlock active in-flight jobs.
3. **Reproducible Distillation**: Distillation pipelines produce verifiable student weights, layer patterns, and quantization receipts that pass reference test oracles.
4. **Fail-Closed Gate Promotion**: Candidate models, evaluation metrics, or heuristic estimators fail closed at promotion boundaries if required baseline evidence or compute probes fail.

5. **Language-specific Semantic Macro Vocabulary**: Build consistently normalized,
independently tested JavaScript and Python solution corpora. Develop at most 256
reusable, parameterized macros per language that compose complete programs for
as many LeetCode problems as supported by evidence. Goals 1a/1b recognize problems
independently of language and retrieve a value with one or more separately tested
implementations; the consumer chooses the language. Goals 2a/2b autonomously
compose familiar and nearby-variant solutions with language-specific macros. People use the same semantic macros through binary
input, counting bindings, constants, control/escape tokens, navigation and
corrections. Graph IR is optional, not the objective. Language codebooks may
differ. Measure representational coverage, autonomous solving and human effort
separately. A whole solution can occupy one of the 256 entries and form a valid
one-macro program; unbounded answer lookup and human steering remain separate
from autonomous macro selection. No vocabulary is presumed optimal.

6. **Literal Composition (3a/3b)**: Keep literal composition separate from the
parameterized macro track. Goal 3a jointly optimizes complete, correct source for
known problems and a reusable dictionary of exact literal strings. Every emitted
character, including names, constants, wrappers, whitespace and punctuation, must
come from the counted encoding; there are no free binding or expression slots.
The pilot covers approximately 20 distinct easy JavaScript problems and varies
vocabulary size while jointly recomposing sources and extracting literal strings.
The owner removed the initial four-bit limit; preserve it as a diagnostic baseline.
There is no free raw-source escape; dictionary and framing costs remain explicit.
Goal 3b later evaluates a frozen literal vocabulary and frozen assembly procedure
on unseen problems or semantic variants. Preserve protected boundaries. Compare
vocabulary cardinality, stored dictionary bytes, program selections, correctness
and search cost on a Pareto frontier. Preserve whole-program literals as a
separate historical baseline; the current 16/32/64/128/256-entry comparison
excludes them from candidate vocabularies. Offline
encoding of supplied solutions is not autonomous assembly from a description.
See the [six-goal contract](projects/algorithm_solver/contracts/literal_composition_goals_v1.json)
and [twenty-program 3a pilot](projects/algorithm_solver/literals/README.md).

## Operating Loops

1. **Empirical Evaluation Loop**:
   ```text
   Ingest Checkpoint -> Run Hardware Probe -> Execute Fixed Evaluation Corpus -> Calculate Scoreboard -> Emit Run Manifest & Receipt
   ```
2. **Capability Transfer Loop (SAME-R)**:
   ```text
   Select Teacher / Student Pair -> Execute Supervised Distillation -> Run Distractor Suites -> Verify Generalization -> Package Artifact
   ```

## Strategic Constraints

- Empirical integrity: Research claims must be backed by exact dataset hashes, seed configurations, and reproducible artifacts.
- Proven hardware probe: An explicit compute probe on ROCm/CUDA must succeed before launching heavy training or evaluation sweeps.
- Independent authority: Gamma does not invent claims for downstream runtimes; Doppler and Doe independently govern their execution environments.

## Lossless Compression Research

**The user retired the entire enwiki9 project on 2026-10-08.** Preserve its source,
contracts and evidence as an archive; stop autonomous research and compute.
[Project status](projects/enwiki9/operations/runtime/project_status.json) is the
current operational authority. Explicit user reopening is required before new
work. The historical objectives and handoffs below remain evidence, not launch
permission. Retirement does not claim objective achievement or impossibility.

For enwiki9, the preserved end-to-end objective is the versioned
[96M complete-byte witness](projects/enwiki9/contracts/research/v4/objective-contract.json):
an exact deterministic full-corpus archive, complete counted package, independent
resource verification, source/license closure and reproducible submission.
The lane's adaptive workflow governs bounded implementation, prediction research,
confirmation and scale decisions; historical 105M, 99M and 90M evidence stays intact.

Before retirement, the enwiki9 priority was a better exported compact model from the preserved
competitive parent, under the 96M target and 95M stretch. Judge actual native
archives and packed-model costs separately before combining the counted total;
keep metadata out of the next training comparison. Preserve the XML/English
census and negative split-stream evidence. Raw category shares and causal donor
availability are measurement inputs, not achievable savings.
Deployment-matched forward computation and fixed-checkpoint numerical attribution
are prerequisites for further enwiki9 training; see the
[numerical comparison](projects/enwiki9/docs/fx2_numeric_attribution_20260919.md).
The [native forward boundary](projects/enwiki9/docs/fx2_native_forward_20260919.md)
passes fixed P/E agreement. The [matched training comparison](projects/enwiki9/docs/fx2_matched_training_20260920.md)
already records a smaller model but larger native payload. The requested forward
correction and data-only versus joint-cost comparison are complete; do not repeat
them as unfinished work. Preserve their bounded component gain without scaling
that training profile or extending its metadata head. The
[complete-trajectory attribution](projects/enwiki9/docs/fx2_training_trajectory_20260920.md)
now shows that trained-position gains survive exactly, while off-window neural
and final-coder losses overwhelm them. This closes fixed P/A/J attribution;
do not repeat it as unfinished parity work. Investigate coverage or preservation
of the parent's off-window predictions before choosing another training profile.
The result does not prove a causal mixer defect or surrogate-gradient cause.
A new training profile needs a distinct frozen hypothesis.
The separately frozen [relational design](projects/enwiki9/operations/adaptive/experiments/fx2_relational_binding_design_q0_v1.json)
tests a new bounded latent binding mechanism against independent bindings and
different causal donors, with the original model preserved. Its
[closed first realization](projects/enwiki9/docs/causal_relational_grammar_20260920.md)
is parked after losses on all three declared populations. The
[donor-coverage comparison](projects/enwiki9/docs/fx2_donor_coverage_20260920.md)
also rejects the tested prefix-transfer realization. Keep cross-history work
parked until a proposal identifies a different decoder-available information
source. Preserve the broader hypothesis without reopening either closed profile.
Complete core delivery and full-corpus prize qualification remain distinct evidence targets.

## Explicit Exclusions

Gamma does not build production end-user applications, client-facing chat widgets, cloud multi-tenant inference services, or unverified marketing benchmarks.

---

Links:
- Strategic intent links to local invariants in [INTENT.md](INTENT.md).
- Technical boundaries and owned authority are chartered in [CATSCAN.md](CATSCAN.md).

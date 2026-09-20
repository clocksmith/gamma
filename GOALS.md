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

For enwiki9, the active end-to-end objective is the versioned
[96M complete-byte witness](projects/enwiki9/contracts/research/v4/objective-contract.json):
an exact deterministic full-corpus archive, complete counted package, independent
resource verification, source/license closure and reproducible submission.
The lane's adaptive workflow governs bounded implementation, prediction research,
confirmation and scale decisions; historical 105M, 99M and 90M evidence stays intact.

The primary enwiki9 direction is joint optimization of a competitive
single-stream predictor's data and packed-weight cost, with decoder-visible
metadata conditioning inside that model and a 95M stretch target. Preserve the
XML/English census and negative split-stream evidence. Raw category shares and
causal donor availability are measurement inputs, not achievable savings.
Deployment-matched forward computation and fixed-checkpoint numerical attribution
are prerequisites for further enwiki9 training; see the
[numerical comparison](projects/enwiki9/docs/fx2_numeric_attribution_20260919.md).

## Explicit Exclusions

Gamma does not build production end-user applications, client-facing chat widgets, cloud multi-tenant inference services, or unverified marketing benchmarks.

---

Links:
- Strategic intent links to local invariants in [INTENT.md](INTENT.md).
- Technical boundaries and owned authority are chartered in [CATSCAN.md](CATSCAN.md).

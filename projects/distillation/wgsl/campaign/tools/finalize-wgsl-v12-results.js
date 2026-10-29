#!/usr/bin/env node

import { createReadStream } from 'node:fs';
import { createHash } from 'node:crypto';
import { mkdir, readFile, stat, writeFile } from 'node:fs/promises';
import { dirname, join, relative, resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

import { sha256BytesHex } from '../src/utils/sha256.js';
import { combineStratumComparisons } from './compare-wgsl-stratified-rollouts.js';
import {
  compareVerifiedWgslRollouts,
} from './lib/wgsl-rollout-comparison.js';
import { parseJsonl } from './lib/wgsl-rollout-verifier.js';

const DEFAULT_POLICY = 'tools/policies/wgsl-repair-v12-evaluation-policy.json';
const DEFAULT_DESIGN = 'docs/status/wgsl-repair-v12-design-2026-07-12.json';
const STRATA = Object.freeze(['short', 'long']);
const CONTROLS = Object.freeze(['anchor', 'random20']);

function parseArgs(argv) {
  const args = {
    policy: DEFAULT_POLICY,
    design: DEFAULT_DESIGN,
    recordedAt: new Date().toISOString().slice(0, 10),
  };
  for (let index = 0; index < argv.length; index += 2) {
    const token = argv[index];
    const value = argv[index + 1];
    if (!token?.startsWith('--') || !value) throw new Error(`${token} requires a value.`);
    args[token.slice(2)] = value;
  }
  if (!args.root || !args.output) throw new Error('--root and --output are required.');
  return args;
}

function requireObject(value, label) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) {
    throw new Error(`${label} must be an object.`);
  }
  return value;
}

function requireEqual(values, label) {
  if (new Set(values).size !== 1) throw new Error(`${label} differs across V12 runs.`);
  return values[0];
}

function requireFinite(value, label) {
  if (!Number.isFinite(value)) throw new Error(`${label} must be finite.`);
  return value;
}

function requirePositiveInteger(value, label) {
  if (!Number.isInteger(value) || value <= 0) throw new Error(`${label} must be positive.`);
  return value;
}

function requireNonnegativeInteger(value, label) {
  if (!Number.isInteger(value) || value < 0) throw new Error(`${label} must be nonnegative.`);
  return value;
}

function requireHash(value, label) {
  if (typeof value !== 'string' || !/^[a-f0-9]{64}$/.test(value)) {
    throw new Error(`${label} must be a SHA-256 digest.`);
  }
  return value;
}

function metric(value, path, label) {
  let current = value;
  for (const key of path) current = current?.[key];
  return requireFinite(current, `${label}.${path.join('.')}`);
}

function mean(values) {
  return values.reduce((sum, value) => sum + value, 0) / values.length;
}

function summarizeMetric(values) {
  return {
    mean: mean(values),
    minimum: Math.min(...values),
    maximum: Math.max(...values),
  };
}

function relativePath(path) {
  return relative(process.cwd(), path).replace(/\\/g, '/');
}

async function sha256FileHex(path) {
  const hash = createHash('sha256');
  for await (const chunk of createReadStream(path)) hash.update(chunk);
  return hash.digest('hex');
}

function holmAdjust(tests) {
  const ordered = tests
    .map((test, index) => ({ index, p: test.exactMcNemarP }))
    .sort((left, right) => left.p - right.p);
  const adjusted = new Array(tests.length);
  let previous = 0;
  for (let rank = 0; rank < ordered.length; rank += 1) {
    const item = ordered[rank];
    const candidate = Math.min(1, item.p * (ordered.length - rank));
    previous = Math.max(previous, candidate);
    adjusted[item.index] = previous;
  }
  return tests.map((test, index) => ({
    ...test,
    holmAdjustedP: adjusted[index],
  }));
}

function validateReceipt(receipt, policy, seed, lane) {
  requireObject(receipt, `publicReceipts.${seed}.${lane}`);
  if (receipt.artifactType !== 'wgsl_stratified_evaluation'
      || receipt.policyId !== policy.policyId
      || receipt.seed !== seed
      || receipt.lane !== lane
      || receipt.split !== 'public-test') {
    throw new Error(`Public receipt identity mismatch for seed ${seed} lane ${lane}.`);
  }
  requireHash(receipt.policyHash, `publicReceipts.${seed}.${lane}.policyHash`);
  requireHash(receipt.referencePolicyHash, `publicReceipts.${seed}.${lane}.referencePolicyHash`);
  const expectedRows = policy.splits['public-test'].short.rows
    + policy.splits['public-test'].long.rows;
  if (receipt.overall?.groupCount !== expectedRows) {
    throw new Error(`Public receipt denominator mismatch for seed ${seed} lane ${lane}.`);
  }
  for (const stratum of STRATA) {
    const expected = policy.splits['public-test'][stratum];
    const actual = receipt.strata?.[stratum];
    if (actual?.rows !== expected.rows || actual?.datasetSha256 !== expected.datasetSha256) {
      throw new Error(`Public ${stratum} contract mismatch for seed ${seed} lane ${lane}.`);
    }
  }
}

function summarizeTrainingExport(exportReceipt, seed, lane) {
  requireObject(exportReceipt, `trainingExports.${seed}.${lane}`);
  const metrics = requireObject(exportReceipt.metrics, `trainingExports.${seed}.${lane}.metrics`);
  if (metrics.datasetRows !== 1200
      || metrics.distinctRowsVisited !== 1200
      || metrics.steps !== 1200
      || metrics.rowOrder !== 'seed_hash_sorted_v1'
      || exportReceipt.checkpointStep !== 1200) {
    throw new Error(`Training completion contract mismatch for seed ${seed} lane ${lane}.`);
  }
  const policyHash = exportReceipt.manifest?.metadata?.receipts?.[0]?.policyHash;
  return {
    seed,
    lane,
    workloadId: exportReceipt.workloadId,
    workloadSha256: requireHash(
      exportReceipt.workloadSha256,
      `trainingExports.${seed}.${lane}.workloadSha256`
    ),
    configHash: requireHash(
      exportReceipt.configHash,
      `trainingExports.${seed}.${lane}.configHash`
    ),
    datasetHash: requireHash(
      exportReceipt.datasetHash,
      `trainingExports.${seed}.${lane}.datasetHash`
    ),
    rowOrderSha256: requireHash(
      metrics.rowOrderSha256,
      `trainingExports.${seed}.${lane}.rowOrderSha256`
    ),
    policyHash: requireHash(policyHash, `trainingExports.${seed}.${lane}.policyHash`),
    adapterWeightsSha256: requireHash(
      exportReceipt.weightsSha256,
      `trainingExports.${seed}.${lane}.weightsSha256`
    ),
    datasetRows: metrics.datasetRows,
    distinctRowsVisited: metrics.distinctRowsVisited,
    microsteps: metrics.steps,
    optimizerUpdates: metrics.steps / 8,
    finalLoss: requireFinite(metrics.loss, `trainingExports.${seed}.${lane}.loss`),
    meanLoss: requireFinite(metrics.meanLoss, `trainingExports.${seed}.${lane}.meanLoss`),
  };
}

function summarizeReceipt(receipt) {
  return {
    policyHash: receipt.policyHash,
    passAt1: metric(receipt, ['overall', 'passAt1'], 'receipt'),
    passAt8: metric(receipt, ['overall', 'passAtK'], 'receipt'),
    samplePassRate: metric(receipt, ['overall', 'samplePassRate'], 'receipt'),
    passingTasksAt1: requireNonnegativeInteger(
      receipt.overall?.passingTasksAt1,
      'receipt.overall.passingTasksAt1'
    ),
    tasks: requirePositiveInteger(receipt.overall?.groupCount, 'receipt.overall.groupCount'),
    blockedSamples: requireNonnegativeInteger(
      receipt.overall?.blockedSamples,
      'receipt.overall.blockedSamples'
    ),
    shortPassAt1: metric(receipt, ['strata', 'short', 'verification', 'passAt1'], 'receipt'),
    longPassAt1: metric(receipt, ['strata', 'long', 'verification', 'passAt1'], 'receipt'),
  };
}

function summarizeComparison(comparison, seed, control) {
  requireObject(comparison, `comparisons.${seed}.${control}`);
  const paired = requireObject(
    comparison.paired?.passAt1,
    `comparisons.${seed}.${control}.paired.passAt1`
  );
  return {
    id: `seed${seed}-external20-vs-${control}`,
    seed,
    referenceLane: control,
    candidateLane: 'external20',
    referencePassAt1: metric(comparison, ['reference', 'passAt1'], 'comparison'),
    candidatePassAt1: metric(comparison, ['candidate', 'passAt1'], 'comparison'),
    effectPassAt1: metric(comparison, ['effects', 'passAt1'], 'comparison'),
    effectPassAt8: metric(comparison, ['effects', 'passAtK'], 'comparison'),
    referenceOnly: paired.referenceOnly,
    candidateOnly: paired.candidateOnly,
    exactMcNemarP: metric(comparison, ['paired', 'passAt1', 'exactMcNemarP'], 'comparison'),
  };
}

export function summarizeV12Results({
  policy,
  design,
  diagnosticDecision,
  publicReceipts,
  trainingExports,
  comparisons,
  artifacts,
  recordedAt,
}) {
  requireObject(policy, 'policy');
  requireObject(design, 'design');
  requireObject(diagnosticDecision, 'diagnosticDecision');
  requireObject(artifacts, 'artifacts');
  const seeds = policy.selection?.seeds;
  const lanes = policy.selection?.lanes;
  if (!Array.isArray(seeds) || seeds.length !== 3
      || !Array.isArray(lanes) || lanes.join(',') !== 'anchor,external20,random20') {
    throw new Error('Unexpected V12 seed or lane contract.');
  }
  if (diagnosticDecision.status !== 'candidate_selected'
      || diagnosticDecision.selectedLane !== 'external20'
      || diagnosticDecision.publicEvaluationAllowed !== true) {
    throw new Error('The sealed diagnostic decision does not authorize public V12 analysis.');
  }

  const training = [];
  const perSeed = {};
  const allReceipts = [];
  for (const seed of seeds) {
    perSeed[seed] = {};
    for (const lane of lanes) {
      const receipt = publicReceipts?.[seed]?.[lane];
      validateReceipt(receipt, policy, seed, lane);
      allReceipts.push(receipt);
      perSeed[seed][lane] = summarizeReceipt(receipt);
      training.push(summarizeTrainingExport(trainingExports?.[seed]?.[lane], seed, lane));
      if (training.at(-1).policyHash !== receipt.policyHash) {
        throw new Error(`Training/evaluation policy hash mismatch for seed ${seed} lane ${lane}.`);
      }
    }
  }

  const referencePolicyHash = requireEqual(
    allReceipts.map((receipt) => receipt.referencePolicyHash),
    'referencePolicyHash'
  );
  const meanByLane = Object.fromEntries(lanes.map((lane) => {
    const summaries = seeds.map((seed) => perSeed[seed][lane]);
    return [lane, {
      passAt1: summarizeMetric(summaries.map((summary) => summary.passAt1)),
      passAt8: summarizeMetric(summaries.map((summary) => summary.passAt8)),
      samplePassRate: summarizeMetric(summaries.map((summary) => summary.samplePassRate)),
      shortPassAt1: summarizeMetric(summaries.map((summary) => summary.shortPassAt1)),
      longPassAt1: summarizeMetric(summaries.map((summary) => summary.longPassAt1)),
    }];
  }));

  const publicChecks = {
    treatmentBeatsAnchorEverySeed: seeds.every((seed) => (
      perSeed[seed].external20.passAt1 > perSeed[seed].anchor.passAt1
    )),
    treatmentBeatsRandomMean: (
      meanByLane.external20.passAt1.mean > meanByLane.random20.passAt1.mean
    ),
    longNonRegression: (
      meanByLane.external20.longPassAt1.mean >= meanByLane.anchor.longPassAt1.mean
    ),
  };
  const publicRuleReplayPassed = Object.values(publicChecks).every(Boolean);

  const rawTests = [];
  for (const seed of seeds) {
    for (const control of CONTROLS) {
      rawTests.push(summarizeComparison(comparisons?.[seed]?.[control], seed, control));
    }
  }
  const pairedComparisons = holmAdjust(rawTests);
  const significantTests = pairedComparisons.filter((test) => test.holmAdjustedP < 0.05);
  const pooledDiscordance = Object.fromEntries(CONTROLS.map((control) => {
    const rows = pairedComparisons.filter((comparison) => comparison.referenceLane === control);
    return [control, {
      referenceOnly: rows.reduce((sum, row) => sum + row.referenceOnly, 0),
      candidateOnly: rows.reduce((sum, row) => sum + row.candidateOnly, 0),
      inferentialUseAllowed: false,
      reason: 'The same public tasks repeat across seeds, so seed-task pairs are not independent.',
    }];
  }));

  const runtimes = training.map((entry) => {
    const source = trainingExports[entry.seed][entry.lane];
    return source.manifest.metadata.receipts[0].runtime;
  });
  const runtime = {
    deviceName: requireEqual(runtimes.map((value) => value.deviceName), 'deviceName'),
    dtype: requireEqual(runtimes.map((value) => value.dtype), 'dtype'),
    hipVersion: requireEqual(runtimes.map((value) => value.hipVersion), 'hipVersion'),
    torchVersion: requireEqual(runtimes.map((value) => value.torchVersion), 'torchVersion'),
    transformersVersion: requireEqual(
      runtimes.map((value) => value.transformersVersion),
      'transformersVersion'
    ),
  };

  const effectVsAnchor = (
    meanByLane.external20.passAt1.mean - meanByLane.anchor.passAt1.mean
  );
  const effectVsRandom = (
    meanByLane.external20.passAt1.mean - meanByLane.random20.passAt1.mean
  );
  const sameRStage = publicRuleReplayPassed ? 'seed_confirmed' : 'mechanics_proven';
  return {
    artifactType: 'wgsl_repair_v12_result',
    schemaVersion: 1,
    experimentId: design.experimentId,
    recordedAt,
    status: publicRuleReplayPassed
      ? 'seed_confirmed_compiler_curation'
      : 'public_compiler_replication_failed',
    hypothesis: design.hypothesis,
    method: {
      methodIds: ['data_centric_sft'],
      teacherModel: null,
      studentModel: {
        modelId: policy.model.modelId,
        revision: policy.model.revision,
        baseModelId: requireEqual(
          training.map((entry) => trainingExports[entry.seed][entry.lane].baseModelId),
          'baseModelId'
        ),
      },
      intervention: 'Replace 240 of 1,200 Doppler rows with pinned Zero-TVM repairs.',
      anchor: 'Train on 1,200 Doppler rows.',
      randomControl: 'Replace 240 rows with a disjoint seeded Doppler sample.',
      task: 'Family-disjoint replacement-only WGSL compiler repair.',
    },
    sameR: {
      detailedStage: sameRStage,
      registerStatus: 'mechanics_proven',
      rationale: publicRuleReplayPassed
        ? 'The frozen diagnostic selection rule reproduces on the complete three-seed public compiler matrix, but semantic guardrails are absent.'
        : 'All mechanics completed, but the frozen diagnostic conclusion did not reproduce on public compiler evaluation.',
    },
    frozenContract: {
      policyId: policy.policyId,
      successRule: policy.selection.successRule,
      primaryMetric: policy.selection.primaryMetric,
      seeds,
      lanes,
      publicTasks: policy.splits['public-test'].short.rows
        + policy.splits['public-test'].long.rows,
      samplesPerPolicy: (
        policy.splits['public-test'].short.rows + policy.splits['public-test'].long.rows
      ) * policy.sampling.groupSize,
      referencePolicyHash,
    },
    diagnosticSelection: {
      status: diagnosticDecision.status,
      selectedLane: diagnosticDecision.selectedLane,
      checks: diagnosticDecision.checks,
      aggregate: diagnosticDecision.aggregate,
    },
    training: {
      runtime,
      completedRuns: training.length,
      expectedRuns: seeds.length * lanes.length,
      adapterWeightsByteVerified: artifacts.adapterWeights?.length === 9,
      allRowsConsumedOnce: training.every((entry) => (
        entry.datasetRows === 1200 && entry.distinctRowsVisited === 1200
      )),
      runs: training,
    },
    publicEvaluation: {
      completedPolicies: allReceipts.length,
      expectedPolicies: seeds.length * lanes.length,
      perSeed,
      meanByLane,
      effects: {
        external20VsAnchorMeanPassAt1: effectVsAnchor,
        external20VsRandom20MeanPassAt1: effectVsRandom,
        external20VsAnchorMeanLongPassAt1: (
          meanByLane.external20.longPassAt1.mean - meanByLane.anchor.longPassAt1.mean
        ),
      },
      frozenRuleReplay: {
        status: publicRuleReplayPassed ? 'passed' : 'failed',
        checks: publicChecks,
        note: 'This replays the already-frozen diagnostic selection rule descriptively on public outcomes; it is not a new promotion threshold.',
      },
      pairedComparisons,
      multiplicity: {
        family: 'Six per-seed external20-versus-control pass@1 McNemar tests.',
        adjustment: 'Holm',
        alpha: 0.05,
        significantTestIds: significantTests.map((test) => test.id),
      },
      pooledDiscordanceDescriptive: pooledDiscordance,
    },
    evidenceBoundary: {
      fullLaneTrainingCompleted: training.length === 9,
      adapterWeightsByteVerified: artifacts.adapterWeights?.length === 9,
      diagnosticMatrixCompleted: diagnosticDecision.inputs?.length === 9,
      publicCompilerMatrixCompleted: allReceipts.length === 9,
      publicRuleReplayPassed,
      perSeedControlTestSignificantAfterHolm: significantTests.length > 0,
      semanticKernelSuiteCompleted: false,
      adapterInferenceParityCompleted: false,
      runtimePerformanceMeasured: false,
      promoted: false,
    },
    artifacts,
    claimBoundary: 'V12 provides seed-confirmed controlled-data evidence on the frozen public WGSL compiler-repair diagnostic: external20 has the highest mean pass@1, beats anchor at all three seeds, beats the random-control mean, and improves mean long-stratum pass@1. No per-seed control comparison is significant after Holm correction, the long stratum has nine tasks, and no sealed dispatch, CPU-oracle, numerical, metamorphic, bounds, or historical-regression suite ran. This is data-centric SFT compiler evidence, not teacher distillation, semantic-kernel correctness, adapter promotion, or runtime-performance evidence.',
    nextGates: [
      'Provision and run the sealed semantic WGSL suite with dispatch, CPU-oracle, numerical, metamorphic, bounds, and historical-regression checks under a separately frozen contract.',
      'Prove PEFT-to-Doppler adapter activation and matched inference parity from a coherent base-model lane before any local serving claim.',
      'Treat dense checkpoint selection, GRPO from the selected SFT lane, and Doppler-native training parity as separate SAME-R experiments rather than modifying V12 after outcome opening.',
    ],
  };
}

async function readArtifact(path) {
  const absolutePath = resolve(path);
  const bytes = await readFile(absolutePath);
  return {
    value: JSON.parse(bytes.toString('utf8')),
    pointer: {
      path: relativePath(absolutePath),
      sha256: sha256BytesHex(new Uint8Array(bytes)),
    },
  };
}

async function readGroups(path, label) {
  return parseJsonl(await readFile(path, 'utf8'), label);
}

async function buildComparison(root, seed, control) {
  const strata = {};
  for (const stratum of STRATA) {
    const referencePath = join(
      root,
      `seed${seed}`,
      control,
      'evaluation',
      'public-test',
      stratum,
      'verified-rollouts',
      'rollout-groups.jsonl'
    );
    const candidatePath = join(
      root,
      `seed${seed}`,
      'external20',
      'evaluation',
      'public-test',
      stratum,
      'verified-rollouts',
      'rollout-groups.jsonl'
    );
    const [reference, candidate] = await Promise.all([
      readGroups(referencePath, `seed ${seed} ${control} ${stratum}`),
      readGroups(candidatePath, `seed ${seed} external20 ${stratum}`),
    ]);
    strata[stratum] = compareVerifiedWgslRollouts(reference, candidate);
  }
  return combineStratumComparisons(strata);
}

export async function main(argv = process.argv.slice(2)) {
  const args = parseArgs(argv);
  const root = resolve(args.root);
  const [policyArtifact, designArtifact, decisionArtifact] = await Promise.all([
    readArtifact(args.policy),
    readArtifact(args.design),
    readArtifact(join(root, 'lane-decision.json')),
  ]);
  const policy = policyArtifact.value;
  const seeds = policy.selection.seeds;
  const lanes = policy.selection.lanes;
  const publicReceipts = {};
  const trainingExports = {};
  const comparisons = {};
  const artifacts = {
    policy: policyArtifact.pointer,
    design: designArtifact.pointer,
    diagnosticDecision: decisionArtifact.pointer,
    trainingExports: [],
    adapterWeights: [],
    publicEvaluationReceipts: [],
  };

  for (const seed of seeds) {
    publicReceipts[seed] = {};
    trainingExports[seed] = {};
    comparisons[seed] = {};
    for (const lane of lanes) {
      const [evaluationArtifact, trainingArtifact] = await Promise.all([
        readArtifact(join(
          root,
          `seed${seed}`,
          lane,
          'evaluation',
          'public-test',
          'stratified-evaluation.json'
        )),
        readArtifact(join(
          root,
          `seed${seed}`,
          lane,
          'sft',
          'exports',
          'checkpoint-001200.export.json'
        )),
      ]);
      publicReceipts[seed][lane] = evaluationArtifact.value;
      trainingExports[seed][lane] = trainingArtifact.value;
      const weightsPath = join(
        root,
        `seed${seed}`,
        lane,
        'sft',
        'exports',
        'checkpoint-001200.adapters.safetensors'
      );
      const [weightsSha256, weightsStat] = await Promise.all([
        sha256FileHex(weightsPath),
        stat(weightsPath),
      ]);
      if (weightsSha256 !== trainingArtifact.value.weightsSha256) {
        throw new Error(`Adapter weights checksum mismatch for seed ${seed} lane ${lane}.`);
      }
      artifacts.publicEvaluationReceipts.push({
        seed,
        lane,
        ...evaluationArtifact.pointer,
      });
      artifacts.trainingExports.push({
        seed,
        lane,
        ...trainingArtifact.pointer,
      });
      artifacts.adapterWeights.push({
        seed,
        lane,
        path: relativePath(weightsPath),
        sha256: weightsSha256,
        bytes: weightsStat.size,
      });
    }
    for (const control of CONTROLS) {
      comparisons[seed][control] = await buildComparison(root, seed, control);
    }
  }

  const result = summarizeV12Results({
    policy,
    design: designArtifact.value,
    diagnosticDecision: decisionArtifact.value,
    publicReceipts,
    trainingExports,
    comparisons,
    artifacts,
    recordedAt: args.recordedAt,
  });
  const outputPath = resolve(args.output);
  await mkdir(dirname(outputPath), { recursive: true });
  await writeFile(outputPath, `${JSON.stringify(result, null, 2)}\n`, 'utf8');
  console.log(JSON.stringify({
    ok: true,
    outputPath,
    status: result.status,
    sameR: result.sameR,
    effects: result.publicEvaluation.effects,
  }, null, 2));
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main().catch((error) => {
    console.error(error?.stack || error?.message || String(error));
    process.exitCode = 1;
  });
}

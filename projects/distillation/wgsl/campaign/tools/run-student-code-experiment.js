#!/usr/bin/env node

import { access, mkdir, readFile, writeFile } from 'node:fs/promises';
import { dirname, join, relative, resolve } from 'node:path';
import process from 'node:process';
import { pathToFileURL } from 'node:url';

import {
  activateLoRAFromTrainingOutputForPipeline,
  unloadLoRAAdapterForPipeline,
} from '../src/client/runtime/lora.js';
import { formatChatMessages } from '../src/inference/pipelines/text/chat-format.js';
import { installNodeFileFetchShim } from '../src/tooling/node-file-fetch.js';
import { bootstrapNodeWebGPU } from '../src/tooling/node-webgpu.js';
import { runLoraPipeline } from '../src/experimental/training/lora-pipeline.js';
import { loadDistillModelHandle } from '../src/experimental/training/suite.js';
import { loadTrainingWorkloadCapsule } from '../src/experimental/training/workloads.js';
import {
  buildOuroborosFailureSignals,
  buildStudentLoraWorkload,
  buildStudentPromotionReport,
  buildStudentReplaySummary,
  buildStudentTrainingDatasets,
  evaluateStudentCandidate,
  loadStudentCodeExperimentContracts,
  renderStudentTaskPrompt,
  selectStudentHoldoutTasks,
  writeJsonArtifact,
  writeJsonlArtifact,
} from './lib/student-code-experiment.js';

const PHASES = Object.freeze(['baseline', 'prepare', 'train', 'replay', 'report', 'all']);
const ADAPTER_VARIANTS = Object.freeze(['javascript', 'wgsl', 'mixed']);

function parseAdapter(value) {
  const separator = value.indexOf('=');
  if (separator <= 0 || separator === value.length - 1) {
    throw new Error('--adapter requires variant=/path/to/runtime-adapter-manifest.json.');
  }
  const variant = value.slice(0, separator);
  if (!ADAPTER_VARIANTS.includes(variant)) {
    throw new Error(`--adapter variant must be one of ${ADAPTER_VARIANTS.join(', ')}.`);
  }
  return {
    variant,
    manifestPath: resolve(value.slice(separator + 1)),
  };
}

function parseVariant(value) {
  const variant = String(value || '');
  if (!ADAPTER_VARIANTS.includes(variant)) {
    throw new Error(`--variant must be one of ${ADAPTER_VARIANTS.join(', ')}.`);
  }
  return variant;
}

function parseArgs(argv) {
  const options = {
    phase: 'all',
    runRoot: null,
    teacherRunRoot: null,
    policyPath: null,
    adapters: [],
    variants: [],
    json: false,
  };
  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    if (arg === '--phase') {
      options.phase = String(argv[index + 1] || '');
      index += 1;
      continue;
    }
    if (arg === '--run-root') {
      options.runRoot = String(argv[index + 1] || '');
      index += 1;
      continue;
    }
    if (arg === '--teacher-run') {
      options.teacherRunRoot = String(argv[index + 1] || '');
      index += 1;
      continue;
    }
    if (arg === '--policy') {
      options.policyPath = String(argv[index + 1] || '');
      index += 1;
      continue;
    }
    if (arg === '--adapter') {
      options.adapters.push(parseAdapter(String(argv[index + 1] || '')));
      index += 1;
      continue;
    }
    if (arg.startsWith('--adapter=')) {
      options.adapters.push(parseAdapter(arg.slice('--adapter='.length)));
      continue;
    }
    if (arg === '--variant') {
      options.variants.push(parseVariant(argv[index + 1]));
      index += 1;
      continue;
    }
    if (arg.startsWith('--variant=')) {
      options.variants.push(parseVariant(arg.slice('--variant='.length)));
      continue;
    }
    if (arg === '--json') {
      options.json = true;
      continue;
    }
    throw new Error(`Unknown argument: ${arg}`);
  }
  if (!PHASES.includes(options.phase)) {
    throw new Error(`--phase must be one of ${PHASES.join(', ')}.`);
  }
  options.variants = [...new Set(options.variants)];
  return options;
}

function defaultRunRoot(root) {
  const timestamp = new Date().toISOString().replaceAll(':', '-');
  return resolve(root, 'reports', 'training', 'student-code-replay', timestamp);
}

async function pathExists(path) {
  try {
    await access(path);
    return true;
  } catch {
    return false;
  }
}

async function collectText(iterable) {
  let output = '';
  for await (const chunk of iterable) output += chunk;
  return output;
}

function countTokens(tokenizer, text) {
  const encoded = tokenizer.encode(text);
  return Array.isArray(encoded) || ArrayBuffer.isView(encoded) ? encoded.length : 0;
}

async function requireGpu() {
  installNodeFileFetchShim();
  const result = await bootstrapNodeWebGPU();
  if (!result?.ok) {
    throw new Error(`Node WebGPU bootstrap failed: ${result?.detail || 'unknown error'}`);
  }
  return result;
}

async function loadStudentPipeline(contracts) {
  const startedAt = performance.now();
  const handle = await loadDistillModelHandle(
    contracts.policy.baseModel.modelRef,
    'student replay'
  );
  return {
    ...handle,
    loadDurationMs: performance.now() - startedAt,
  };
}

async function writeReplayReceipt(artifactRoot, row) {
  const { patch, ...receipt } = row;
  await Promise.all([
    writeJsonArtifact(join(artifactRoot, 'receipt.json'), receipt),
    writeFile(join(artifactRoot, 'repair.patch'), patch, 'utf8'),
  ]);
  return receipt;
}

async function replayVariant(options) {
  const {
    contracts,
    pipeline,
    variant,
    adapterManifestPath,
    runRoot,
    loadDurationMs,
  } = options;
  if (adapterManifestPath) {
    await activateLoRAFromTrainingOutputForPipeline(pipeline, {
      adapterManifestPath,
    });
  } else {
    await unloadLoRAAdapterForPipeline(pipeline);
  }
  const adapter = contracts.policy.adapters.find((entry) => entry.id === variant);
  const lanes = variant === 'baseline' ? contracts.policy.lanes : adapter.lanes;
  const tasks = selectStudentHoldoutTasks(contracts, lanes);
  const prompts = new Map();
  for (const task of tasks) {
    // Holdout prompts are rendered once from pinned mutated bytes, then reused verbatim.
    // eslint-disable-next-line no-await-in-loop
    prompts.set(task.id, await renderStudentTaskPrompt(contracts, task));
  }
  const rows = [];
  for (const task of tasks) {
    const prompt = prompts.get(task.id);
    for (
      let repetition = 1;
      repetition <= contracts.policy.generation.repetitions;
      repetition += 1
    ) {
      pipeline.reset();
      const generationStartedAt = performance.now();
      // Replays are serialized so KV state and adapter activation cannot cross tasks.
      // eslint-disable-next-line no-await-in-loop
      const rawOutput = await collectText(pipeline.generate(
        [{ role: 'user', content: prompt }],
        {
          useChatTemplate: true,
          maxTokens: contracts.policy.generation.maxTokens,
          temperature: contracts.policy.generation.temperature,
          topK: contracts.policy.generation.topK,
          topP: contracts.policy.generation.topP,
          repetitionPenalty: contracts.policy.generation.repetitionPenalty,
          seed: contracts.policy.generation.seed,
        }
      ));
      const generationDurationMs = performance.now() - generationStartedAt;
      const renderedPrompt = formatChatMessages(
        [{ role: 'user', content: prompt }],
        contracts.policy.baseModel.chatTemplate
      );
      const performanceReceipt = {
        modelLoadDurationMs: loadDurationMs,
        generationDurationMs,
        promptTokens: countTokens(pipeline.tokenizer, renderedPrompt),
        completionTokens: countTokens(pipeline.tokenizer, rawOutput),
      };
      const artifactRoot = join(
        runRoot,
        'replay',
        variant,
        task.id,
        `repeat-${String(repetition).padStart(2, '0')}`
      );
      await mkdir(artifactRoot, { recursive: true });
      await Promise.all([
        writeFile(join(artifactRoot, 'prompt.txt'), `${prompt}\n`, 'utf8'),
        writeFile(join(artifactRoot, 'output.txt'), rawOutput, 'utf8'),
      ]);
      // eslint-disable-next-line no-await-in-loop
      const evaluated = await evaluateStudentCandidate({
        contracts,
        task,
        rawOutput,
        variant,
        repetition,
        prompt,
      });
      const row = {
        ...evaluated,
        adapterManifestPath: adapterManifestPath || null,
        performance: performanceReceipt,
      };
      // eslint-disable-next-line no-await-in-loop
      await writeReplayReceipt(artifactRoot, row);
      rows.push(row);
      console.error(
        `[student-replay] variant=${variant} lane=${task.lane} task=${task.id} `
        + `repeat=${repetition} pass=${row.passed}`
      );
    }
  }
  const receiptsPath = join(runRoot, 'replay', variant, 'receipts.json');
  const persistedRows = rows.map(({ patch, ...row }) => row);
  await writeJsonArtifact(receiptsPath, persistedRows);
  const summary = buildStudentReplaySummary(variant, rows);
  await writeJsonArtifact(join(runRoot, 'replay', variant, 'summary.json'), summary);
  return rows;
}

async function runBaseline(contracts, runRoot) {
  await requireGpu();
  const handle = await loadStudentPipeline(contracts);
  try {
    return await replayVariant({
      contracts,
      pipeline: handle.pipeline,
      variant: 'baseline',
      adapterManifestPath: null,
      runRoot,
      loadDurationMs: handle.loadDurationMs,
    });
  } finally {
    await handle.pipeline.unload();
  }
}

function serializeDatasetRow(row) {
  return {
    id: row.id,
    prompt: row.prompt,
    completion: row.completion,
    lane: row.lane,
    taskId: row.taskId,
    datasetPass: row.datasetPass,
    teacherModelId: row.teacherModelId,
    teacherProvider: row.teacherProvider,
    qualificationReceipt: row.qualificationReceipt,
    promptHash: row.promptHash,
    completionHash: row.completionHash,
    taskBankHash: row.taskBankHash,
    policyHash: row.policyHash,
    evidenceClass: row.evidenceClass,
  };
}

async function prepareTraining(contracts, runRoot, teacherRunRoot) {
  if (!teacherRunRoot) {
    throw new Error('--teacher-run is required for the prepare and all phases.');
  }
  const bundle = await buildStudentTrainingDatasets({
    contracts,
    teacherRunRoot,
  });
  const index = {
    artifactType: 'student_code_training_index',
    schemaVersion: 1,
    source: 'doppler',
    experimentId: contracts.policy.policyId,
    teacherRun: bundle.teacherRun,
    eligibleAcceptedLabelCount: bundle.eligibleAcceptedLabelCount,
    eligibleAcceptedLaneCounts: bundle.eligibleAcceptedLaneCounts,
    acceptedLabelCount: bundle.acceptedLabelCount,
    acceptedLaneCounts: bundle.acceptedLaneCounts,
    adapters: {},
  };
  for (const adapterId of ADAPTER_VARIANTS) {
    const dataset = bundle.datasets[adapterId];
    const datasetPath = join(runRoot, 'datasets', `${adapterId}.jsonl`);
    const workloadPath = join(runRoot, 'workloads', `${adapterId}.json`);
    await writeJsonlArtifact(datasetPath, dataset.rows.map(serializeDatasetRow));
    const workload = buildStudentLoraWorkload(
      contracts,
      adapterId,
      datasetPath,
      dataset.materializedRowCount
    );
    await writeJsonArtifact(workloadPath, workload);
    await loadTrainingWorkloadCapsule(workloadPath);
    index.adapters[adapterId] = {
      datasetPath: resolve(datasetPath),
      workloadPath: resolve(workloadPath),
      sourceRowCount: dataset.sourceRowCount,
      materializedRowCount: dataset.materializedRowCount,
      laneCounts: dataset.laneCounts,
    };
  }
  await Promise.all([
    writeJsonArtifact(join(runRoot, 'datasets', 'bundle.json'), {
      ...bundle,
      datasets: Object.fromEntries(Object.entries(bundle.datasets).map(([id, dataset]) => [
        id,
        {
          adapter: dataset.adapter,
          sourceRowCount: dataset.sourceRowCount,
          materializedRowCount: dataset.materializedRowCount,
          laneCounts: dataset.laneCounts,
        },
      ])),
    }),
    writeJsonArtifact(join(runRoot, 'training-index.json'), index),
  ]);
  console.error(
    `[student-prepare] eligible=${bundle.eligibleAcceptedLabelCount} `
    + `accepted=${bundle.acceptedLabelCount} `
    + `javascript=${bundle.acceptedLaneCounts.javascript} wgsl=${bundle.acceptedLaneCounts.wgsl}`
  );
  return index;
}

async function readTrainingIndex(runRoot) {
  return JSON.parse(await readFile(join(runRoot, 'training-index.json'), 'utf8'));
}

function buildLearningReceipt(result, expectedSteps) {
  const metrics = Array.isArray(result.metrics) ? result.metrics : [];
  const nonzeroGradientSteps = metrics.filter((entry) => (
    Number.isFinite(entry.gradient_norm_unclipped)
    && entry.gradient_norm_unclipped > 0
  )).length;
  const parameterizedSteps = metrics.filter((entry) => (
    Number.isInteger(entry.total_param_count)
    && entry.total_param_count > 0
  )).length;
  const parameterReceipt = result?.parameterReceipt || null;
  const parameterDeltasPassed = parameterReceipt?.aggregateChanged === true
    && parameterReceipt.tensorCount > 0
    && parameterReceipt.changedTensorCount === parameterReceipt.tensorCount
    && parameterReceipt.nonzeroFinalTensorCount === parameterReceipt.tensorCount
    && Number.isFinite(parameterReceipt.l2Delta)
    && parameterReceipt.l2Delta > 0;
  const evalReports = Array.isArray(result?.evalReports) ? result.evalReports : [];
  const baselineReport = evalReports.find((report) => report.stage === 'base_model') || null;
  const adapterReports = evalReports.filter((report) => report.stage !== 'base_model');
  const adapterReport = adapterReports[adapterReports.length - 1] || null;
  const baselineLoss = Number(baselineReport?.loss);
  const adapterLoss = Number(adapterReport?.loss);
  const absoluteLossImprovement = baselineLoss - adapterLoss;
  const lossImproved = Number.isFinite(baselineLoss)
    && Number.isFinite(adapterLoss)
    && Number.isFinite(absoluteLossImprovement)
    && absoluteLossImprovement >= 1e-6
    && adapterReport?.qualityClaim?.improved === true;
  return {
    expectedSteps,
    observedSteps: metrics.length,
    nonzeroGradientSteps,
    parameterizedSteps,
    parameterDeltas: parameterReceipt,
    parameterDeltasPassed,
    loss: {
      evalDatasetId: adapterReport?.evalDatasetId || baselineReport?.evalDatasetId || null,
      baseline: Number.isFinite(baselineLoss) ? baselineLoss : null,
      adapter: Number.isFinite(adapterLoss) ? adapterLoss : null,
      absoluteImprovement: Number.isFinite(absoluteLossImprovement)
        ? absoluteLossImprovement
        : null,
      improved: lossImproved,
    },
    passed: metrics.length === expectedSteps
      && nonzeroGradientSteps === metrics.length
      && parameterizedSteps === metrics.length
      && parameterDeltasPassed
      && lossImproved,
  };
}

async function trainAdapters(
  contracts,
  runRoot,
  inputIndex = null,
  variants = ADAPTER_VARIANTS
) {
  await requireGpu();
  const trainingIndex = inputIndex || await readTrainingIndex(runRoot);
  const adapterIndexPath = join(runRoot, 'adapter-index.json');
  const adapterIndex = await pathExists(adapterIndexPath)
    ? JSON.parse(await readFile(adapterIndexPath, 'utf8'))
    : {
      artifactType: 'student_code_adapter_index',
      schemaVersion: 1,
      source: 'doppler',
      experimentId: contracts.policy.policyId,
      baseModelId: contracts.policy.baseModel.id,
      adapters: {},
    };
  if (
    adapterIndex.experimentId !== contracts.policy.policyId
    || adapterIndex.baseModelId !== contracts.policy.baseModel.id
  ) {
    throw new Error('existing adapter index does not match the active student experiment.');
  }
  for (const adapterId of variants) {
    const entry = trainingIndex.adapters[adapterId];
    if (!entry) {
      throw new Error(`training index is missing adapter ${adapterId}.`);
    }
    const loadedWorkload = await loadTrainingWorkloadCapsule(entry.workloadPath);
    const startedAt = performance.now();
    console.error(
      `[student-train] adapter=${adapterId} rows=${entry.materializedRowCount} start`
    );
    // Adapter runs are serialized to keep GPU ownership and checkpoint lineage isolated.
    // eslint-disable-next-line no-await-in-loop
    const result = await runLoraPipeline({
      loadedWorkload,
      runRoot: join(runRoot, 'training', adapterId),
    });
    const trainingDurationMs = performance.now() - startedAt;
    const exported = result.exports?.[result.exports.length - 1];
    if (!exported?.runtimeManifestPath) {
      throw new Error(`student adapter ${adapterId} did not export a runtime manifest.`);
    }
    const resultPath = join(runRoot, 'training', adapterId, 'student-training-result.json');
    const learningReceipt = buildLearningReceipt(result, entry.materializedRowCount);
    await writeJsonArtifact(resultPath, {
      ...result,
      trainingDurationMs,
      learningReceipt,
    });
    if (!learningReceipt.passed) {
      throw new Error(
        `student adapter ${adapterId} failed the learning receipt: `
        + `${learningReceipt.nonzeroGradientSteps}/${learningReceipt.observedSteps} nonzero-gradient steps, `
        + `${learningReceipt.parameterizedSteps}/${learningReceipt.observedSteps} parameterized steps, `
        + `parameter_deltas=${learningReceipt.parameterDeltasPassed}, `
        + `loss_improved=${learningReceipt.loss.improved}.`
      );
    }
    adapterIndex.adapters[adapterId] = {
      adapterId,
      workloadPath: entry.workloadPath,
      runRoot: result.runRoot,
      resultPath: resolve(resultPath),
      runtimeManifestPath: resolve(exported.runtimeManifestPath),
      weightsPath: resolve(exported.weightsPath),
      weightsSha256: exported.weightsSha256,
      checkpointId: exported.checkpointId,
      trainingDurationMs,
      trainingSteps: result.metrics?.length ?? null,
      learningReceipt,
      sourceRowCount: entry.sourceRowCount,
      materializedRowCount: entry.materializedRowCount,
      laneCounts: entry.laneCounts,
    };
    console.error(
      `[student-train] adapter=${adapterId} checkpoint=${exported.checkpointId} complete`
    );
  }
  const weightHashes = Object.values(adapterIndex.adapters).map((entry) => entry.weightsSha256);
  if (new Set(weightHashes).size !== weightHashes.length) {
    throw new Error('student adapters exported duplicate weight hashes across distinct datasets.');
  }
  await writeJsonArtifact(adapterIndexPath, adapterIndex);
  return adapterIndex;
}

async function readAdapterIndex(runRoot, explicitAdapters) {
  const explicit = Object.fromEntries(explicitAdapters.map((entry) => [
    entry.variant,
    {
      adapterId: entry.variant,
      runtimeManifestPath: entry.manifestPath,
      source: 'cli',
    },
  ]));
  if (Object.keys(explicit).length > 0) {
    return { adapters: explicit };
  }
  return JSON.parse(await readFile(join(runRoot, 'adapter-index.json'), 'utf8'));
}

async function runAdapterReplays(
  contracts,
  runRoot,
  adapterIndex,
  variants = ADAPTER_VARIANTS
) {
  await requireGpu();
  const handle = await loadStudentPipeline(contracts);
  const rows = [];
  try {
    for (const variant of variants) {
      const adapter = adapterIndex.adapters[variant];
      if (!adapter?.runtimeManifestPath) {
        throw new Error(`adapter index is missing runtime manifest for ${variant}.`);
      }
      // eslint-disable-next-line no-await-in-loop
      const variantRows = await replayVariant({
        contracts,
        pipeline: handle.pipeline,
        variant,
        adapterManifestPath: adapter.runtimeManifestPath,
        runRoot,
        loadDurationMs: handle.loadDurationMs,
      });
      rows.push(...variantRows);
    }
  } finally {
    await handle.pipeline.unload();
  }
  return rows;
}

async function readReplayRows(runRoot) {
  const rows = [];
  for (const variant of ['baseline', ...ADAPTER_VARIANTS]) {
    const path = join(runRoot, 'replay', variant, 'receipts.json');
    if (!(await pathExists(path))) continue;
    // eslint-disable-next-line no-await-in-loop
    const parsed = JSON.parse(await readFile(path, 'utf8'));
    if (!Array.isArray(parsed)) {
      throw new Error(`student replay receipts must be an array: ${path}`);
    }
    rows.push(...parsed);
  }
  return rows;
}

function renderReportMarkdown(report) {
  const lines = [
    '# Doppler student code replay',
    '',
    `Evidence: ${report.promotion.evidenceClass}`,
    '',
    '| Variant | Lane | Constructive pass | Patch applies | Violations | Deterministic | Decode tok/s |',
    '| --- | --- | ---: | ---: | ---: | --- | ---: |',
  ];
  for (const [variant, summary] of Object.entries(report.summaries)) {
    for (const lane of ['javascript', 'wgsl']) {
      const row = summary.byLane[lane];
      if (row.replayCount === 0) continue;
      lines.push(
        `| ${variant} | ${lane} | ${row.passedReplays}/${row.replayCount} `
        + `(${row.constructivePassRate.toFixed(3)}) | ${row.applicableReplays}/${row.replayCount} `
        + `| ${row.policyViolationCount} | ${row.deterministicOutputs ? 'yes' : 'no'} `
        + `| ${row.performance.decodeTokensPerSecond?.toFixed(2) ?? 'n/a'} |`
      );
    }
  }
  lines.push('', '## Promotion gate', '');
  lines.push(`- Control proven: ${report.promotion.controlProven ? 'yes' : 'no'}`);
  for (const [candidateId, candidate] of Object.entries(report.promotion.candidates)) {
    lines.push(`- ${candidateId}: ${candidate.eligible ? 'eligible' : 'experimental'}`);
  }
  lines.push('', '## Failure-only next round', '');
  lines.push(`- Redacted observed failure signals: ${report.failureSignalCount}`);
  lines.push('- Holdout prompts, paths, outputs, and recovery edits are excluded from the queue.');
  return `${lines.join('\n')}\n`;
}

async function writeFinalReport(contracts, runRoot) {
  const rows = await readReplayRows(runRoot);
  if (!rows.some((row) => row.variant === 'baseline')) {
    throw new Error('final student report requires baseline replay receipts.');
  }
  const summaries = {};
  for (const variant of ['baseline', ...ADAPTER_VARIANTS]) {
    if (rows.some((row) => row.variant === variant)) {
      summaries[variant] = buildStudentReplaySummary(variant, rows);
    }
  }
  const promotion = buildStudentPromotionReport(contracts.policy, summaries);
  const failureSignals = buildOuroborosFailureSignals(rows, contracts.policy.policyId);
  const failureQueuePath = join(runRoot, 'ouroboros-failure-signals.jsonl');
  await writeJsonlArtifact(failureQueuePath, failureSignals);
  const report = {
    artifactType: 'student_code_experiment_report',
    schemaVersion: 1,
    source: 'doppler',
    experimentId: contracts.policy.policyId,
    releaseTarget: contracts.policy.releaseTarget,
    claimBoundary: contracts.policy.claimBoundary,
    generatedAt: new Date().toISOString(),
    runRoot: relative(contracts.root, runRoot).replaceAll('\\', '/'),
    summaries,
    promotion,
    failureSignalCount: failureSignals.length,
    failureQueuePath: relative(contracts.root, failureQueuePath).replaceAll('\\', '/'),
  };
  await Promise.all([
    writeJsonArtifact(join(runRoot, 'report.json'), report),
    writeFile(join(runRoot, 'report.md'), renderReportMarkdown(report), 'utf8'),
  ]);
  return report;
}

async function writeRunContract(contracts, runRoot, options) {
  const contractPath = join(runRoot, 'run-contract.json');
  const revision = await runHostRevision(contracts.root);
  let existing = null;
  if (await pathExists(contractPath)) {
    existing = JSON.parse(await readFile(contractPath, 'utf8'));
    if (
      existing.policyHash !== contracts.policyHash
      || existing.taskBankHash !== contracts.host.taskBankArtifact.hash
      || existing.baseModelId !== contracts.policy.baseModel.id
    ) {
      throw new Error('existing run contract does not match the active student experiment.');
    }
  }
  const previousPhases = Array.isArray(existing?.phases)
    ? existing.phases
    : (existing?.phase ? [existing.phase] : []);
  const phases = previousPhases.includes(options.phase)
    ? previousPhases
    : [...previousPhases, options.phase];
  const adapterVariants = [...new Set([
    ...(Array.isArray(existing?.adapterVariants) ? existing.adapterVariants : []),
    ...(options.variants.length > 0 ? options.variants : ADAPTER_VARIANTS),
  ])];
  const existingFields = { ...(existing || {}) };
  delete existingFields.phase;
  const contract = {
    ...existingFields,
    artifactType: 'student_code_experiment_run_contract',
    schemaVersion: 1,
    source: 'doppler',
    experimentId: contracts.policy.policyId,
    releaseTarget: contracts.policy.releaseTarget,
    claimBoundary: contracts.policy.claimBoundary,
    policyPath: contracts.policyPath,
    policyHash: contracts.policyHash,
    taskBankId: contracts.host.taskBank.bankId,
    taskBankHash: contracts.host.taskBankArtifact.hash,
    baseRevision: contracts.host.taskBank.baseRevision,
    harnessHash: contracts.harnessHash,
    harnessFiles: contracts.harnessFiles,
    hostHarnessHash: contracts.host.harnessHash,
    baseModelId: contracts.policy.baseModel.id,
    phases,
    adapterVariants,
    repositoryRevision: revision,
    runtime: {
      nodeVersion: process.version,
      platform: process.platform,
      architecture: process.arch,
    },
  };
  await writeJsonArtifact(contractPath, contract);
  return contract;
}

async function runHostRevision(root) {
  const result = await import('./lib/host-teacher-process.js').then(({ runHostProcess }) => (
    runHostProcess('git', ['rev-parse', 'HEAD'], { cwd: root })
  ));
  if (result.code !== 0 || result.signal) {
    throw new Error('failed to resolve repository revision for student run contract.');
  }
  return result.stdout.trim();
}

export async function main(argv = process.argv.slice(2)) {
  const options = parseArgs(argv);
  const contracts = await loadStudentCodeExperimentContracts({
    policyPath: options.policyPath || undefined,
  });
  const runRoot = options.runRoot ? resolve(options.runRoot) : defaultRunRoot(contracts.root);
  await mkdir(runRoot, { recursive: true });
  await writeRunContract(contracts, runRoot, options);

  let trainingIndex = null;
  let adapterIndex = null;
  const selectedVariants = options.variants.length > 0
    ? options.variants
    : (options.adapters.length > 0
      ? [...new Set(options.adapters.map((adapter) => adapter.variant))]
      : ADAPTER_VARIANTS);
  if (options.phase === 'baseline' || options.phase === 'all') {
    await runBaseline(contracts, runRoot);
  }
  if (options.phase === 'prepare' || options.phase === 'all') {
    trainingIndex = await prepareTraining(
      contracts,
      runRoot,
      options.teacherRunRoot
    );
  }
  if (options.phase === 'train' || options.phase === 'all') {
    if (!trainingIndex && !(await pathExists(join(runRoot, 'training-index.json')))) {
      trainingIndex = await prepareTraining(
        contracts,
        runRoot,
        options.teacherRunRoot
      );
    }
    adapterIndex = await trainAdapters(
      contracts,
      runRoot,
      trainingIndex,
      selectedVariants
    );
  }
  if (options.phase === 'replay' || options.phase === 'all') {
    adapterIndex ||= await readAdapterIndex(runRoot, options.adapters);
    await runAdapterReplays(contracts, runRoot, adapterIndex, selectedVariants);
  }
  let report = null;
  if (['baseline', 'replay', 'report', 'all'].includes(options.phase)) {
    report = await writeFinalReport(contracts, runRoot);
  }
  const result = {
    ok: true,
    phase: options.phase,
    runRoot,
    reportPath: report ? join(runRoot, 'report.json') : null,
    controlProven: report?.promotion.controlProven ?? null,
  };
  if (options.json) {
    console.log(JSON.stringify(result, null, 2));
  } else {
    console.log(
      `student-code-experiment: ${options.phase} complete; run=${runRoot}; `
      + `control=${result.controlProven == null ? 'not-evaluated' : result.controlProven}`
    );
  }
  return result;
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main().catch((error) => {
    console.error(error?.stack || error?.message || String(error));
    process.exitCode = 1;
  });
}

#!/usr/bin/env node

import { createHash } from 'node:crypto';
import { execFile } from 'node:child_process';
import fs from 'node:fs/promises';
import path from 'node:path';
import { promisify } from 'node:util';
import { pathToFileURL } from 'node:url';

import { hashWgslSemanticEvidenceValue } from '../src/tooling/wgsl-repair-semantic-gate.js';
import {
  compareFloatArrays,
  exactTokenComparison,
  l2Norm,
  subtractFloatArrays,
  topKTokenOverlap,
} from './compare-wgsl-repair-adapter-parity.js';
import { buildGammaProcessEnv } from './trainers/gamma-wgsl-trainer.js';

const execFileAsync = promisify(execFile);
const DEFAULT_POLICY = 'tools/policies/wgsl-writer-v2-parity-policy.json';
const REFERENCE_RUNNER = 'tools/wgsl-repair-peft-parity-reference.py';
const DOPPLER_RUNNER = 'tools/inspect-prefill-logits.js';

function parseArgs(argv) {
  const args = {
    policyPath: DEFAULT_POLICY,
    sourceModelPath: String(process.env.GAMMA_WGSL_MODEL_PATH || '').trim(),
    dopplerModelPath: String(process.env.DOPPLER_WGSL_MODEL_PATH || '').trim(),
    outputRoot: '',
  };
  for (let index = 0; index < argv.length; index += 1) {
    const token = argv[index];
    if (token === '--policy') args.policyPath = argv[++index] || '';
    else if (token === '--source-model') args.sourceModelPath = argv[++index] || '';
    else if (token === '--doppler-model') args.dopplerModelPath = argv[++index] || '';
    else if (token === '--out-root') args.outputRoot = argv[++index] || '';
    else throw new Error(`Unknown argument: ${token}`);
  }
  if (!args.sourceModelPath) {
    throw new Error('--source-model or GAMMA_WGSL_MODEL_PATH is required.');
  }
  if (!args.dopplerModelPath) {
    throw new Error('--doppler-model or DOPPLER_WGSL_MODEL_PATH is required.');
  }
  return args;
}

async function readJson(filePath) {
  return JSON.parse(await fs.readFile(path.resolve(filePath), 'utf8'));
}

async function sha256File(filePath) {
  return createHash('sha256').update(await fs.readFile(path.resolve(filePath))).digest('hex');
}

function sha256Text(value) {
  return createHash('sha256').update(String(value)).digest('hex');
}

function requireInternalHash(value, label) {
  const core = { ...value };
  const expected = core.receiptHash;
  delete core.receiptHash;
  if (expected !== hashWgslSemanticEvidenceValue(core)) {
    throw new Error(`${label} internal receipt hash mismatch.`);
  }
}

function requireTrainingStatusHash(value, label) {
  const core = { ...value };
  const expected = core.receiptHash;
  delete core.receiptHash;
  const actual = createHash('sha256').update(JSON.stringify(core)).digest('hex');
  if (expected !== actual) throw new Error(`${label} internal receipt hash mismatch.`);
}

async function requireFileHash(filePath, expectedSha256, label) {
  const actual = await sha256File(filePath);
  if (actual !== expectedSha256) {
    throw new Error(`${label} SHA-256 mismatch: expected ${expectedSha256}, got ${actual}.`);
  }
}

async function requireAbsent(filePath) {
  try {
    await fs.access(path.resolve(filePath));
  } catch (error) {
    if (error?.code === 'ENOENT') return;
    throw error;
  }
  throw new Error(`Writer adapter parity is already sealed: ${filePath}`);
}

async function readFloat32(filePath) {
  const bytes = await fs.readFile(path.resolve(filePath));
  if (bytes.byteLength % Float32Array.BYTES_PER_ELEMENT !== 0) {
    throw new Error(`${filePath} is not a complete Float32 capture.`);
  }
  const buffer = bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength);
  return new Float32Array(buffer);
}

async function readProbe(policy) {
  await requireFileHash(policy.probe.datasetPath, policy.probe.datasetSha256, 'parity probe');
  const lines = (await fs.readFile(path.resolve(policy.probe.datasetPath), 'utf8'))
    .split(/\r?\n/)
    .filter((line) => line.trim());
  const row = JSON.parse(lines[policy.probe.rowIndex]);
  if ((row.rowId || row.taskId || row.id) !== policy.probe.rowId
    || sha256Text(row.prompt) !== policy.probe.promptSha256) {
    throw new Error('Writer parity probe identity mismatch.');
  }
  return row;
}

async function loadCandidate(policy) {
  const [selection, confirmation] = await Promise.all([
    readJson(policy.predecessor.selectionReceiptPath),
    readJson(policy.predecessor.confirmationReceiptPath),
  ]);
  requireInternalHash(selection, 'writer seed selection');
  requireInternalHash(confirmation, 'writer seed confirmation');
  if (selection.decision !== 'seed_selected'
    || confirmation.decision !== 'seed_confirmation_passed'
    || confirmation.selectedAdapter?.seed !== selection.selected.seed) {
    throw new Error('Writer parity requires a selected and seed-confirmed adapter.');
  }
  const status = await readJson(selection.selected.trainingStatusPath);
  requireTrainingStatusHash(status, 'selected writer training status');
  if (status.decision !== 'training_complete'
    || status.seed !== selection.selected.seed
    || status.gammaReceipt?.adapterPath !== selection.selected.adapterPath
    || status.gammaReceipt?.policyHash !== selection.selected.adapterTreeSha256) {
    throw new Error('Selected writer adapter is not bound to its training receipt.');
  }
  await Promise.all([
    requireFileHash(
      status.export.manifestPath,
      status.export.manifestSha256,
      'selected Doppler adapter manifest'
    ),
    requireFileHash(
      status.export.weightsPath,
      status.export.weightsSha256,
      'selected Doppler adapter weights'
    ),
  ]);
  return { selection, confirmation, status };
}

async function runProcess(executable, argv, options) {
  let result;
  try {
    result = await execFileAsync(executable, argv, {
      cwd: process.cwd(),
      env: options.env || process.env,
      encoding: 'utf8',
      maxBuffer: 32 * 1024 * 1024,
    });
  } catch (error) {
    await Promise.all([
      fs.writeFile(options.stdoutPath, String(error?.stdout || ''), 'utf8'),
      fs.writeFile(options.stderrPath, String(error?.stderr || error), 'utf8'),
    ]);
    throw error;
  }
  await Promise.all([
    fs.writeFile(options.stdoutPath, result.stdout || '', 'utf8'),
    fs.writeFile(options.stderrPath, result.stderr || '', 'utf8'),
  ]);
}

async function runReference(args, policy, candidate, outputRoot) {
  const gammaRoot = path.resolve(process.env.GAMMA_ROOT || path.join(process.cwd(), '..', 'gamma'));
  const python = path.resolve(
    process.env.GAMMA_WGSL_PYTHON || path.join(gammaRoot, '.venv_rocm', 'bin', 'python')
  );
  const outputPath = path.join(outputRoot, 'transformers', 'reference.json');
  const logitsDir = path.join(outputRoot, 'transformers');
  await fs.mkdir(logitsDir, { recursive: true });
  try {
    return { path: outputPath, receipt: await readJson(outputPath) };
  } catch (error) {
    if (error?.code !== 'ENOENT') throw error;
  }
  await runProcess(python, [
    path.resolve(REFERENCE_RUNNER),
    '--model', path.resolve(args.sourceModelPath),
    '--model-revision', policy.sourceModel.revision,
    '--dataset', path.resolve(policy.probe.datasetPath),
    '--row-index', String(policy.probe.rowIndex),
    '--adapter', `${candidate.status.seed}=${candidate.status.gammaReceipt.adapterPath}`,
    '--dtype', policy.sourceModel.referenceDtype,
    '--max-new-tokens', String(policy.probe.generation.maxNewTokens),
    '--logits-dir', path.resolve(logitsDir),
    '--out', path.resolve(outputPath),
  ], {
    env: buildGammaProcessEnv(),
    stdoutPath: path.join(logitsDir, 'stdout.log'),
    stderrPath: path.join(logitsDir, 'stderr.log'),
  });
  return { path: outputPath, receipt: await readJson(outputPath) };
}

async function runDopplerCapture(options) {
  const outputPath = path.join(options.outputRoot, `${options.id}.json`);
  const logitsPath = path.join(options.outputRoot, `${options.id}.first-token-logits.f32`);
  try {
    return { path: outputPath, receipt: await readJson(outputPath) };
  } catch (error) {
    if (error?.code !== 'ENOENT') throw error;
  }
  const argv = [
    path.resolve(DOPPLER_RUNNER),
    '--model-dir', path.resolve(options.args.dopplerModelPath),
    '--model-id', options.policy.dopplerBaseArtifact.modelId,
    '--prompt', options.prompt,
    '--runtime-profile', options.policy.dopplerBaseArtifact.runtimeProfile,
    '--top-k', '20',
    '--max-tokens', String(options.policy.probe.generation.maxNewTokens),
    '--no-chat-template',
    '--out', path.resolve(outputPath),
    '--logits-out', path.resolve(logitsPath),
  ];
  if (options.adapterManifestPath) {
    argv.push('--adapter-manifest', path.resolve(options.adapterManifestPath));
  }
  await runProcess(process.execPath, argv, {
    stdoutPath: path.join(options.outputRoot, `${options.id}.stdout.log`),
    stderrPath: path.join(options.outputRoot, `${options.id}.stderr.log`),
  });
  return { path: outputPath, receipt: await readJson(outputPath) };
}

function evaluateBase(policy, reference, doppler, referenceLogits, dopplerLogits) {
  const promptTokens = exactTokenComparison(
    reference.probe.promptTokenIds,
    doppler.promptTokens?.ids
  );
  const logits = compareFloatArrays(referenceLogits, dopplerLogits);
  const topK = topKTokenOverlap(reference.base.topK, doppler.topK, policy.thresholds.topK);
  const completionTokens = exactTokenComparison(
    reference.base.completionTokenIds,
    doppler.generation?.tokenIds
  );
  const checks = {
    promptTokenIdsExact: promptTokens.exact,
    firstTokenIdExact: reference.base.selectedTokenId === doppler.selectedToken?.tokenId,
    logitsFinite: logits.finite,
    logitCosineSimilarity:
      logits.cosineSimilarity >= policy.thresholds.base.minimumLogitCosineSimilarity,
    topKTokenOverlap: topK.overlap >= policy.thresholds.base.minimumTopKTokenOverlap,
  };
  return {
    pass: Object.values(checks).every(Boolean),
    checks,
    promptTokens,
    logits,
    topK,
    completion: {
      tokens: completionTokens,
      textExact: reference.base.completionText === doppler.generation?.output,
    },
  };
}

function evaluateAdapter(options) {
  const thresholds = options.policy.thresholds.adapter;
  const promptTokens = exactTokenComparison(
    options.reference.probe.promptTokenIds,
    options.doppler.promptTokens?.ids
  );
  const completionTokens = exactTokenComparison(
    options.referenceAdapter.completionTokenIds,
    options.doppler.generation?.tokenIds
  );
  const logits = compareFloatArrays(options.referenceAdapterLogits, options.dopplerAdapterLogits);
  const topK = topKTokenOverlap(
    options.referenceAdapter.topK,
    options.doppler.topK,
    options.policy.thresholds.topK
  );
  const referenceDelta = subtractFloatArrays(
    options.referenceAdapterLogits,
    options.referenceBaseLogits
  );
  const dopplerDelta = subtractFloatArrays(
    options.dopplerAdapterLogits,
    options.dopplerBaseLogits
  );
  const delta = compareFloatArrays(referenceDelta, dopplerDelta);
  const checks = {
    promptTokenIdsExact: promptTokens.exact,
    firstTokenIdExact:
      options.referenceAdapter.selectedTokenId === options.doppler.selectedToken?.tokenId,
    completionTokenIdsExact: completionTokens.exact,
    completionTextExact:
      options.referenceAdapter.completionText === options.doppler.generation?.output,
    logitsFinite: logits.finite,
    logitCosineSimilarity: logits.cosineSimilarity >= thresholds.minimumLogitCosineSimilarity,
    topKTokenOverlap: topK.overlap >= thresholds.minimumTopKTokenOverlap,
    adapterDeltaFinite: delta.finite,
    adapterDeltaCosineSimilarity:
      delta.cosineSimilarity >= thresholds.minimumAdapterDeltaCosineSimilarity,
    referenceAdapterDeltaNonzero:
      l2Norm(referenceDelta) >= thresholds.minimumNonzeroAdapterDeltaL2Norm,
    dopplerAdapterDeltaNonzero:
      l2Norm(dopplerDelta) >= thresholds.minimumNonzeroAdapterDeltaL2Norm,
  };
  return {
    pass: Object.values(checks).every(Boolean),
    checks,
    promptTokens,
    completionTokens,
    logits,
    topK,
    adapterDelta: {
      ...delta,
      referenceL2Norm: l2Norm(referenceDelta),
      dopplerL2Norm: l2Norm(dopplerDelta),
    },
  };
}

async function validateIdentities(args, policy, probe, candidate, reference, base, adapter) {
  const referenceAdapter = reference.adapters[0];
  const checks = {
    sourceConfig: reference.model.configSha256 === policy.sourceModel.configSha256,
    sourceTokenizer: reference.model.tokenizerSha256 === policy.sourceModel.tokenizerSha256,
    sourceRevision: reference.model.revision === policy.sourceModel.revision,
    probeDataset: reference.probe.datasetSha256 === policy.probe.datasetSha256,
    probeRow: reference.probe.rowId === policy.probe.rowId,
    prompt: reference.probe.promptSha256 === policy.probe.promptSha256
      && sha256Text(base.prompt) === policy.probe.promptSha256
      && sha256Text(adapter.prompt) === policy.probe.promptSha256
      && probe.prompt === base.prompt
      && probe.prompt === adapter.prompt,
    dopplerManifest:
      base.artifactFiles?.['manifest.json']?.sha256
        === policy.dopplerBaseArtifact.manifestSha256
      && adapter.artifactFiles?.['manifest.json']?.sha256
        === policy.dopplerBaseArtifact.manifestSha256,
    dopplerTokenizer:
      base.artifactFiles?.['tokenizer.json']?.sha256
        === policy.dopplerBaseArtifact.tokenizerSha256
      && adapter.artifactFiles?.['tokenizer.json']?.sha256
        === policy.dopplerBaseArtifact.tokenizerSha256,
    referenceAdapterWeights:
      referenceAdapter.adapterWeightsSha256
        === await sha256File(path.join(candidate.status.gammaReceipt.adapterPath, 'adapter_model.safetensors')),
    dopplerAdapterManifest:
      adapter.adapter?.artifact?.manifestSha256 === candidate.status.export.manifestSha256,
    dopplerAdapterWeights:
      adapter.adapter?.artifact?.weightsSha256 === candidate.status.export.weightsSha256,
    adapterActivated: adapter.adapter?.activation?.activated === true,
  };
  return { pass: Object.values(checks).every(Boolean), checks };
}

export async function runWgslWriterV2Parity(args) {
  const policy = await readJson(args.policyPath);
  if (policy?.policyId !== 'doppler-wgsl-writer-v2-selected-adapter-parity'
    || policy.status !== 'frozen_before_checkpoint_selection') {
    throw new Error('Writer parity requires the frozen writer-v2 parity policy.');
  }
  await requireFileHash(
    policy.predecessor.trainingPolicy.path,
    policy.predecessor.trainingPolicy.sha256,
    'writer training policy'
  );
  const outputRoot = path.resolve(
    args.outputRoot
      || 'reports/training/wgsl-writer/doppler-wgsl-writer-v2/evaluation/parity'
  );
  const receiptPath = path.join(outputRoot, 'parity.json');
  await requireAbsent(receiptPath);
  await Promise.all([
    requireFileHash(
      path.join(args.sourceModelPath, 'config.json'),
      policy.sourceModel.configSha256,
      'source config'
    ),
    requireFileHash(
      path.join(args.sourceModelPath, 'tokenizer.json'),
      policy.sourceModel.tokenizerSha256,
      'source tokenizer'
    ),
    requireFileHash(
      path.join(args.dopplerModelPath, 'manifest.json'),
      policy.dopplerBaseArtifact.manifestSha256,
      'Doppler model manifest'
    ),
    requireFileHash(
      path.join(args.dopplerModelPath, 'tokenizer.json'),
      policy.dopplerBaseArtifact.tokenizerSha256,
      'Doppler tokenizer'
    ),
  ]);
  await fs.mkdir(outputRoot, { recursive: true });
  const [probe, candidate] = await Promise.all([readProbe(policy), loadCandidate(policy)]);
  const referenceEntry = await runReference(args, policy, candidate, outputRoot);
  const dopplerRoot = path.join(outputRoot, 'doppler');
  await fs.mkdir(dopplerRoot, { recursive: true });
  const baseEntry = await runDopplerCapture({
    id: 'base',
    args,
    policy,
    prompt: probe.prompt,
    outputRoot: dopplerRoot,
    adapterManifestPath: null,
  });
  const adapterEntry = await runDopplerCapture({
    id: `seed${candidate.status.seed}`,
    args,
    policy,
    prompt: probe.prompt,
    outputRoot: dopplerRoot,
    adapterManifestPath: candidate.status.export.manifestPath,
  });
  const reference = referenceEntry.receipt;
  const referenceAdapter = reference.adapters[0];
  const referenceBaseLogits = await readFloat32(reference.base.logits.path);
  const referenceAdapterLogits = await readFloat32(referenceAdapter.logits.path);
  const dopplerBaseLogits = await readFloat32(baseEntry.receipt.logitsCapture.path);
  const dopplerAdapterLogits = await readFloat32(adapterEntry.receipt.logitsCapture.path);
  const identities = await validateIdentities(
    args,
    policy,
    probe,
    candidate,
    reference,
    baseEntry.receipt,
    adapterEntry.receipt
  );
  const base = evaluateBase(
    policy,
    reference,
    baseEntry.receipt,
    referenceBaseLogits,
    dopplerBaseLogits
  );
  const adapter = evaluateAdapter({
    policy,
    reference,
    referenceAdapter,
    doppler: adapterEntry.receipt,
    referenceBaseLogits,
    dopplerBaseLogits,
    referenceAdapterLogits,
    dopplerAdapterLogits,
  });
  const pass = identities.pass && base.pass && adapter.pass;
  const core = {
    schema: 'doppler.wgsl-writer-adapter-parity-receipt/v1',
    experimentId: policy.experimentId,
    policy: { path: args.policyPath, sha256: await sha256File(args.policyPath) },
    selection: {
      path: policy.predecessor.selectionReceiptPath,
      sha256: await sha256File(policy.predecessor.selectionReceiptPath),
      receiptHash: candidate.selection.receiptHash,
      selectedSeed: candidate.status.seed,
    },
    confirmation: {
      path: policy.predecessor.confirmationReceiptPath,
      sha256: await sha256File(policy.predecessor.confirmationReceiptPath),
      receiptHash: candidate.confirmation.receiptHash,
    },
    evidence: {
      reference: { path: referenceEntry.path, sha256: await sha256File(referenceEntry.path) },
      dopplerBase: { path: baseEntry.path, sha256: await sha256File(baseEntry.path) },
      dopplerAdapter: { path: adapterEntry.path, sha256: await sha256File(adapterEntry.path) },
    },
    identities,
    base,
    adapter,
    decision: pass ? 'selected_adapter_parity_passed' : 'selected_adapter_parity_failed',
    seedConfirmationSatisfied: true,
    dopplerParitySatisfied: pass,
    promotionAuthority: false,
    generalWgslWriterClaim: false,
    claimBoundary: policy.claimBoundary,
  };
  const receipt = { ...core, receiptHash: hashWgslSemanticEvidenceValue(core) };
  await fs.writeFile(receiptPath, `${JSON.stringify(receipt, null, 2)}\n`, 'utf8');
  return { ok: pass, receiptPath, receipt };
}

async function main() {
  const result = await runWgslWriterV2Parity(parseArgs(process.argv.slice(2)));
  process.stdout.write(`${JSON.stringify(result, null, 2)}\n`);
  if (!result.ok) process.exitCode = 1;
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main().catch((error) => {
    console.error(error instanceof Error ? error.stack : String(error));
    process.exitCode = 1;
  });
}

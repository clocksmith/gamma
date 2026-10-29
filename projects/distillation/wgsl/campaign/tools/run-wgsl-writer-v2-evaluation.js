#!/usr/bin/env node

import { createHash } from 'node:crypto';
import { execFile } from 'node:child_process';
import fs from 'node:fs/promises';
import path from 'node:path';
import { promisify } from 'node:util';
import { pathToFileURL } from 'node:url';

import {
  evaluateWgslSemanticTaskEvidence,
  hashWgslSemanticEvidenceValue,
  normalizeWgslSemanticEvidenceValue,
} from '../src/tooling/wgsl-repair-semantic-gate.js';
import { createWgslBrowserVerifier } from './lib/wgsl-browser-verifier.js';
import {
  runWgslWriterTaskManifest,
  summarizeWgslSemanticTaskEvidence,
} from './lib/wgsl-writer-semantic-harness.js';
import { buildGammaProcessEnv } from './trainers/gamma-wgsl-trainer.js';

const execFileAsync = promisify(execFile);
const DEFAULT_POLICY = 'tools/policies/wgsl-writer-v2-training-policy.json';
const REFERENCE_RUNNER = 'tools/wgsl-writer-peft-reference.py';
const ROLE_CONFIG = Object.freeze({
  calibration: {
    policyKey: 'calibration',
    corpusKey: 'calibration',
    manifestRole: 'calibration',
    priorRole: null,
  },
  'checkpoint-selection': {
    policyKey: 'checkpointSelection',
    corpusKey: 'checkpoint_selection',
    manifestRole: 'checkpoint_selection',
    priorRole: 'calibration',
  },
  'seed-confirmation': {
    policyKey: 'seedConfirmation',
    corpusKey: 'seed_confirmation',
    manifestRole: 'seed_confirmation',
    priorRole: 'checkpoint-selection',
  },
});

function parseArgs(argv) {
  const args = {
    policyPath: DEFAULT_POLICY,
    role: '',
    modelPath: String(process.env.GAMMA_WGSL_MODEL_PATH || '').trim(),
    outputRoot: '',
  };
  for (let index = 0; index < argv.length; index += 1) {
    const token = argv[index];
    if (token === '--policy') args.policyPath = argv[++index] || '';
    else if (token === '--role') args.role = argv[++index] || '';
    else if (token === '--model') args.modelPath = argv[++index] || '';
    else if (token === '--out-root') args.outputRoot = argv[++index] || '';
    else throw new Error(`Unknown argument: ${token}`);
  }
  if (!ROLE_CONFIG[args.role]) {
    throw new Error('--role must be calibration, checkpoint-selection, or seed-confirmation.');
  }
  if (!args.modelPath) throw new Error('--model or GAMMA_WGSL_MODEL_PATH is required.');
  return args;
}

async function readJson(filePath) {
  return JSON.parse(await fs.readFile(path.resolve(filePath), 'utf8'));
}

async function sha256File(filePath) {
  const bytes = await fs.readFile(path.resolve(filePath));
  return createHash('sha256').update(bytes).digest('hex');
}

function sha256Value(value) {
  return createHash('sha256').update(JSON.stringify(value)).digest('hex');
}

async function requireFileHash(filePath, expectedSha256, label) {
  const actual = await sha256File(filePath);
  if (actual !== expectedSha256) {
    throw new Error(`${label} SHA-256 mismatch: expected ${expectedSha256}, got ${actual}.`);
  }
  return actual;
}

function requireInternalHash(value, hashField, label) {
  const core = { ...value };
  const expected = core[hashField];
  delete core[hashField];
  if (expected !== sha256Value(core)) throw new Error(`${label} internal hash mismatch.`);
}

function requireStableInternalHash(value, hashField, label) {
  const core = { ...value };
  const expected = core[hashField];
  delete core[hashField];
  if (expected !== hashWgslSemanticEvidenceValue(core)) {
    throw new Error(`${label} internal hash mismatch.`);
  }
}

async function pathAbsent(filePath, label) {
  try {
    await fs.access(path.resolve(filePath));
  } catch (error) {
    if (error?.code === 'ENOENT') return;
    throw error;
  }
  throw new Error(`${label} already exists; each candidate permits one submission: ${filePath}`);
}

async function loadTrainingCandidates(policy) {
  const candidates = [];
  for (const workload of policy.workloads) {
    const statusPath = path.join(workload.runRoot, 'training-status.json');
    const status = await readJson(statusPath);
    requireInternalHash(status, 'receiptHash', `seed ${workload.seed} training status`);
    if (status.decision !== 'training_complete'
      || status.seed !== workload.seed
      || status.workload?.sha256 !== workload.sha256) {
      throw new Error(`Seed ${workload.seed} is not admitted for evaluation.`);
    }
    const adapterPath = status.gammaReceipt?.adapterPath;
    const adapterTreeSha256 = status.gammaReceipt?.policyHash;
    if (!adapterPath || !adapterTreeSha256) {
      throw new Error(`Seed ${workload.seed} has no Gamma adapter identity.`);
    }
    await Promise.all([
      requireFileHash(
        path.join(adapterPath, 'adapter_model.safetensors'),
        status.gammaReceipt.adapterWeightsSha256
          || await sha256File(path.join(adapterPath, 'adapter_model.safetensors')),
        `seed ${workload.seed} PEFT weights`
      ),
      requireFileHash(workload.path, workload.sha256, `seed ${workload.seed} workload`),
    ]);
    candidates.push({
      seed: workload.seed,
      adapterPath,
      adapterTreeSha256,
      statusPath,
      statusSha256: await sha256File(statusPath),
    });
  }
  return candidates;
}

async function loadEvaluationInputs(policy, role) {
  const roleConfig = ROLE_CONFIG[role];
  const corpusPolicy = await readJson(policy.admission.corpusPolicy.path);
  const corpusManifest = await readJson(policy.admission.corpusManifest.path);
  await Promise.all([
    requireFileHash(
      policy.admission.corpusPolicy.path,
      policy.admission.corpusPolicy.sha256,
      'writer corpus policy'
    ),
    requireFileHash(
      policy.admission.corpusManifest.path,
      policy.admission.corpusManifest.sha256,
      'writer corpus manifest'
    ),
    requireFileHash(
      corpusPolicy.predecessor.mechanicsPolicy.path,
      corpusPolicy.predecessor.mechanicsPolicy.sha256,
      'writer semantic predecessor policy'
    ),
  ]);
  requireInternalHash(corpusManifest, 'manifestSha256', 'writer corpus manifest');
  const semanticPolicy = await readJson(corpusPolicy.predecessor.mechanicsPolicy.path);
  const rolePolicy = policy.evaluation[roleConfig.policyKey];
  const corpusRole = corpusManifest.roles[roleConfig.corpusKey];
  if (rolePolicy.populationPath !== corpusRole.taskManifestPath
    || rolePolicy.rows !== corpusRole.rows) {
    throw new Error(`${role} population is not bound to the frozen corpus manifest.`);
  }
  const manifestBinding = corpusManifest.fileBindings[corpusRole.taskManifestPath];
  await Promise.all([
    requireFileHash(
      corpusRole.datasetPath,
      corpusRole.datasetSha256,
      `${role} generation dataset`
    ),
    requireFileHash(
      corpusRole.taskManifestPath,
      manifestBinding.sha256,
      `${role} semantic task manifest`
    ),
  ]);
  const manifest = await readJson(corpusRole.taskManifestPath);
  if (manifest.role !== roleConfig.manifestRole
    || manifest.tasks?.length !== rolePolicy.rows) {
    throw new Error(`${role} semantic task manifest contract mismatch.`);
  }
  return { corpusManifest, corpusRole, manifest, manifestBinding, semanticPolicy };
}

async function loadReferenceShaders(manifest) {
  const references = {};
  for (const task of manifest.tasks) {
    await requireFileHash(
      task.referenceShaderPath,
      task.referenceShaderSha256,
      `${task.taskId} reference shader`
    );
    references[task.taskId] = (
      await fs.readFile(path.resolve(task.referenceShaderPath), 'utf8')
    ).trim();
  }
  return references;
}

async function requirePriorGate(outputBase, role, policy) {
  const priorRole = ROLE_CONFIG[role].priorRole;
  if (!priorRole) return null;
  if (role === 'seed-confirmation') {
    const selectionPath = path.join(outputBase, 'selection', 'selected-seed.json');
    const selection = await readJson(selectionPath);
    requireStableInternalHash(selection, 'receiptHash', 'writer seed selection');
    if (selection.decision !== 'seed_selected'
      || selection.policy?.sha256 !== await sha256File(policy.path)) {
      throw new Error('Seed confirmation is blocked until frozen checkpoint selection completes.');
    }
    return { path: selectionPath, sha256: await sha256File(selectionPath) };
  }
  const priorPath = path.join(outputBase, priorRole, 'evaluation.json');
  const prior = await readJson(priorPath);
  requireStableInternalHash(prior, 'receiptHash', `${priorRole} evaluation`);
  if (prior.decision !== 'evaluation_complete') {
    throw new Error(`${role} is blocked by incomplete ${priorRole}.`);
  }
  return { path: priorPath, sha256: await sha256File(priorPath) };
}

function referenceProcessArgs(options) {
  const args = [
    path.resolve(REFERENCE_RUNNER),
    '--model', path.resolve(options.modelPath),
    '--model-revision', options.policy.model.revision,
    '--dataset', path.resolve(options.corpusRole.datasetPath),
    '--dtype', options.policy.trainer.dtype,
    '--max-new-tokens', String(options.policy.generation.maxTokens),
    '--evaluation-role', ROLE_CONFIG[options.role].manifestRole,
    '--out', path.resolve(options.referencePath),
  ];
  for (const candidate of options.candidates) {
    args.push('--adapter', `${candidate.seed}=${path.resolve(candidate.adapterPath)}`);
  }
  return args;
}

async function runReference(options) {
  try {
    return await readJson(options.referencePath);
  } catch (error) {
    if (error?.code !== 'ENOENT') throw error;
  }
  const gammaRoot = path.resolve(process.env.GAMMA_ROOT || path.join(process.cwd(), '..', 'gamma'));
  const python = path.resolve(
    process.env.GAMMA_WGSL_PYTHON || path.join(gammaRoot, '.venv_rocm', 'bin', 'python')
  );
  let result;
  try {
    result = await execFileAsync(python, referenceProcessArgs(options), {
      cwd: process.cwd(),
      env: buildGammaProcessEnv(),
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
  return readJson(options.referencePath);
}

async function readExistingCandidateReceipt(receiptPath, options) {
  let receipt;
  try {
    receipt = await readJson(receiptPath);
  } catch (error) {
    if (error?.code === 'ENOENT') return null;
    throw error;
  }
  requireStableInternalHash(receipt, 'receiptHash', `seed ${options.seed} semantic receipt`);
  if (receipt.policy?.sha256 !== options.policySha256
    || receipt.population?.sha256 !== options.populationSha256
    || receipt.reference?.sha256 !== options.referenceSha256
    || receipt.candidate?.seed !== options.seed
    || receipt.submission?.ordinalForCandidate !== 1) {
    throw new Error(`Seed ${options.seed} existing semantic receipt is stale.`);
  }
  return receipt;
}

export function summarizeWriterCandidate(tasks, evaluatedTasks, completions) {
  const count = tasks.length;
  const semanticPasses = evaluatedTasks.filter((task) => task.pass).length;
  const compilePasses = tasks.filter((task) => task.compilation?.status === 'pass').length;
  const responsePasses = tasks.filter((task) => task.responseContractPass === true).length;
  const policyViolations = tasks.filter((task) => (
    Array.isArray(task.responseContractViolations)
      && task.responseContractViolations.length > 0
  )).length;
  const characterCount = tasks.reduce((sum, task) => (
    sum + String(completions?.[task.taskId] || '').length
  ), 0);
  return {
    taskCount: count,
    semanticPasses,
    semanticPassRate: semanticPasses / count,
    compilePasses,
    compilePassRate: compilePasses / count,
    responseContractPasses: responsePasses,
    responseContractPassRate: responsePasses / count,
    meanShaderCharacterCount: characterCount / count,
    policyViolationTasks: policyViolations,
    policyViolationRate: policyViolations / count,
  };
}

async function evaluateCandidate(options) {
  const tasks = await runWgslWriterTaskManifest({
    manifest: options.manifest,
    referenceShaders: options.referenceShaders,
    mode: 'candidate',
    completions: options.referenceCandidate.completions,
    responseContract: options.semanticPolicy.taskContract.responseEnvelope,
    verifier: options.verifier,
  });
  const evaluatedTasks = tasks.map((task) => (
    evaluateWgslSemanticTaskEvidence(options.semanticPolicy, task)
  ));
  const summary = summarizeWriterCandidate(
    tasks,
    evaluatedTasks,
    options.referenceCandidate.completions
  );
  const core = {
    schema: 'doppler.wgsl-writer-semantic-evaluation/v1',
    experimentId: options.policy.experimentId,
    evaluationRole: ROLE_CONFIG[options.role].manifestRole,
    policy: options.policyIdentity,
    population: options.populationIdentity,
    candidate: options.candidate,
    reference: options.referenceIdentity,
    runtime: {
      backend: 'chromium_webgpu',
      deviceInfo: options.verifier.deviceInfo,
      browserArgs: options.verifier.browserArgs,
    },
    tasks,
    evaluatedTasks,
    delegatedSummary: summarizeWgslSemanticTaskEvidence(tasks),
    summary,
    submission: {
      ordinalForCandidate: 1,
      retryPerformed: false,
      promptOrSamplerChangedAfterFreeze: false,
    },
    decision: 'candidate_evaluation_complete',
    selectionEvidence: options.role === 'checkpoint-selection',
    confirmationEvidence: options.role === 'seed-confirmation',
    promotionAuthority: false,
    generalWgslWriterClaim: false,
    claimBoundary: options.policy.claimBoundary,
  };
  const serializableCore = normalizeWgslSemanticEvidenceValue(core);
  return {
    ...serializableCore,
    receiptHash: hashWgslSemanticEvidenceValue(serializableCore),
  };
}

export async function runWgslWriterV2Evaluation(args) {
  const policy = await readJson(args.policyPath);
  if (policy?.policyId !== 'doppler-wgsl-writer-v2-training') {
    throw new Error('WGSL writer v2 evaluation requires the frozen training policy.');
  }
  policy.path = args.policyPath;
  const outputBase = path.resolve(
    args.outputRoot || path.join('reports/training/wgsl-writer', policy.experimentId, 'evaluation')
  );
  const roleRoot = path.join(outputBase, args.role);
  const evaluationPath = path.join(roleRoot, 'evaluation.json');
  const referencePath = path.join(roleRoot, 'peft-reference.json');
  await pathAbsent(evaluationPath, `${args.role} evaluation`);
  await fs.mkdir(roleRoot, { recursive: true });
  const [inputs, candidates, priorGate] = await Promise.all([
    loadEvaluationInputs(policy, args.role),
    loadTrainingCandidates(policy),
    requirePriorGate(outputBase, args.role, policy),
  ]);
  const policyIdentity = { path: args.policyPath, sha256: await sha256File(args.policyPath) };
  const populationIdentity = {
    path: inputs.corpusRole.taskManifestPath,
    sha256: inputs.manifestBinding.sha256,
    datasetPath: inputs.corpusRole.datasetPath,
    datasetSha256: inputs.corpusRole.datasetSha256,
    rows: inputs.corpusRole.rows,
  };
  const stdoutPath = path.join(roleRoot, 'peft-reference.stdout.log');
  const stderrPath = path.join(roleRoot, 'peft-reference.stderr.log');
  const reference = await runReference({
    policy,
    role: args.role,
    modelPath: args.modelPath,
    corpusRole: inputs.corpusRole,
    candidates,
    referencePath,
    stdoutPath,
    stderrPath,
  });
  if (reference.dataset?.sha256 !== inputs.corpusRole.datasetSha256
    || reference.model?.revision !== policy.model.revision
    || reference.candidates?.length !== candidates.length) {
    throw new Error('Transformers/PEFT reference is not bound to the frozen evaluation inputs.');
  }
  const referenceIdentity = { path: referencePath, sha256: await sha256File(referencePath) };
  const referenceShaders = await loadReferenceShaders(inputs.manifest);
  const verifier = await createWgslBrowserVerifier({
    requiredFeatures: [],
    progressEvery: 16,
  });
  const receipts = [];
  try {
    for (const candidate of candidates) {
      const referenceCandidate = reference.candidates.find((entry) => entry.seed === candidate.seed);
      if (!referenceCandidate
        || referenceCandidate.adapterTreeSha256 !== candidate.adapterTreeSha256) {
        throw new Error(`Seed ${candidate.seed} reference adapter identity mismatch.`);
      }
      const receiptPath = path.join(roleRoot, `seed${candidate.seed}.semantic.json`);
      let receipt = await readExistingCandidateReceipt(receiptPath, {
        seed: candidate.seed,
        policySha256: policyIdentity.sha256,
        populationSha256: populationIdentity.sha256,
        referenceSha256: referenceIdentity.sha256,
      });
      if (!receipt) {
        receipt = await evaluateCandidate({
          policy,
          role: args.role,
          semanticPolicy: inputs.semanticPolicy,
          manifest: inputs.manifest,
          referenceShaders,
          verifier,
          referenceCandidate,
          candidate,
          policyIdentity,
          populationIdentity,
          referenceIdentity,
        });
        await fs.writeFile(receiptPath, `${JSON.stringify(receipt, null, 2)}\n`, 'utf8');
      }
      receipts.push({
        seed: candidate.seed,
        path: path.relative(process.cwd(), receiptPath),
        sha256: await sha256File(receiptPath),
        receiptHash: receipt.receiptHash,
        summary: receipt.summary,
      });
    }
  } finally {
    await verifier.close();
  }
  const core = {
    schema: 'doppler.wgsl-writer-evaluation-batch/v1',
    experimentId: policy.experimentId,
    evaluationRole: ROLE_CONFIG[args.role].manifestRole,
    policy: policyIdentity,
    population: populationIdentity,
    priorGate,
    runner: {
      orchestratorPath: 'tools/run-wgsl-writer-v2-evaluation.js',
      orchestratorSha256: await sha256File('tools/run-wgsl-writer-v2-evaluation.js'),
      referencePath: REFERENCE_RUNNER,
      referenceSha256: await sha256File(REFERENCE_RUNNER),
    },
    reference: referenceIdentity,
    candidates: receipts,
    decision: 'evaluation_complete',
    selectionAuthority: args.role === 'checkpoint-selection',
    confirmationAuthority: args.role === 'seed-confirmation',
    promotionAuthority: false,
    claimBoundary: policy.claimBoundary,
  };
  const receipt = { ...core, receiptHash: hashWgslSemanticEvidenceValue(core) };
  await fs.writeFile(evaluationPath, `${JSON.stringify(receipt, null, 2)}\n`, 'utf8');
  return { ok: true, evaluationPath, receipt };
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  process.stdout.write(`${JSON.stringify(await runWgslWriterV2Evaluation(args), null, 2)}\n`);
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main().catch((error) => {
    console.error(error instanceof Error ? error.stack : String(error));
    process.exitCode = 1;
  });
}

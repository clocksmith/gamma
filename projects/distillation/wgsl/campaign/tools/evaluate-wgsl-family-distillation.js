#!/usr/bin/env node

import { execFile } from 'node:child_process';
import { createHash } from 'node:crypto';
import fs from 'node:fs/promises';
import path from 'node:path';
import { promisify } from 'node:util';
import { pathToFileURL } from 'node:url';

import { hashWgslSemanticEvidenceValue } from '../src/tooling/wgsl-repair-semantic-gate.js';
import { createWgslAuthorBrowserExecutor } from './lib/wgsl-author-browser-executor.js';
import { buildGammaProcessEnv } from './trainers/gamma-wgsl-trainer.js';
import {
  candidateSummary,
  evaluateCompletion,
} from './run-wgsl-writer-v3-evaluation.js';

const execFileAsync = promisify(execFile);
const ROOT = path.resolve(import.meta.dirname, '..');
const POLICY_PATH = path.join(ROOT, 'tools/policies/wgsl-writer-family-distillation-policy.json');
const CORPUS_MANIFEST_PATH = path.join(
  ROOT,
  'reports/training/wgsl-writer/doppler-wgsl-writer-v3/corpus-v4-explicit-budget/corpus-manifest.json',
);
const REFERENCE_RUNNER = path.join(ROOT, 'tools/wgsl-writer-peft-reference.py');
const ROLE_KEYS = new Set(['checkpoint_selection', 'seed_confirmation']);

function parseArgs(argv) {
  const args = {
    role: 'checkpoint_selection',
    modelPath: '',
    outputRoot: '',
    referenceBatchSize: 4,
  };
  for (let index = 0; index < argv.length; index += 1) {
    const token = argv[index];
    if (token === '--role') args.role = argv[++index] || '';
    else if (token === '--model') args.modelPath = argv[++index] || '';
    else if (token === '--out-root') args.outputRoot = argv[++index] || '';
    else if (token === '--reference-batch-size') {
      args.referenceBatchSize = Number.parseInt(argv[++index] || '', 10);
    }
    else throw new Error(`Unknown argument: ${token}`);
  }
  if (!ROLE_KEYS.has(args.role)) {
    throw new Error('--role must be checkpoint_selection or seed_confirmation');
  }
  if (!args.modelPath) throw new Error('--model is required');
  if (!Number.isInteger(args.referenceBatchSize) || args.referenceBatchSize < 1) {
    throw new Error('--reference-batch-size must be a positive integer');
  }
  return args;
}

async function readJson(filePath) {
  return JSON.parse(await fs.readFile(filePath, 'utf8'));
}

async function sha256File(filePath) {
  return createHash('sha256').update(await fs.readFile(filePath)).digest('hex');
}

async function runReference(options) {
  try {
    return await readJson(options.outputPath);
  } catch (error) {
    if (error?.code !== 'ENOENT') throw error;
  }
  const python = path.resolve(
    process.env.GAMMA_WGSL_PYTHON
      || path.join(ROOT, '..', 'gamma', '.venv_rocm', 'bin', 'python')
  );
  const args = [
    REFERENCE_RUNNER,
    '--model', path.resolve(options.modelPath),
    '--model-revision', options.student.revision,
    '--dataset', path.resolve(options.datasetPath),
    '--dtype', 'bfloat16',
    '--max-new-tokens', String(options.policy.evaluation.generation.maxNewTokens),
    '--batch-size', String(options.referenceBatchSize),
    '--evaluation-role', options.role,
    '--experiment-id', options.policy.policyId,
    '--out', options.outputPath,
    '--adapter', `0=${path.resolve(options.policy.arms[0].adapterPath)}`,
  ];
  for (const arm of options.policy.arms) {
    args.push('--candidate', `${arm.id}=${path.resolve(arm.adapterPath)}`);
  }
  const result = await execFileAsync(python, args, {
    cwd: ROOT,
    env: buildGammaProcessEnv(),
    encoding: 'utf8',
    maxBuffer: 32 * 1024 * 1024,
  });
  await Promise.all([
    fs.writeFile(`${options.outputPath}.stdout.log`, result.stdout || '', 'utf8'),
    fs.writeFile(`${options.outputPath}.stderr.log`, result.stderr || '', 'utf8'),
  ]);
  return readJson(options.outputPath);
}

export async function evaluateFamilyDistillation(args) {
  const [policy, corpusManifest] = await Promise.all([
    readJson(POLICY_PATH),
    readJson(CORPUS_MANIFEST_PATH),
  ]);
  if (policy.policyId !== 'doppler-wgsl-writer-family-distillation-v1') {
    throw new Error('family-distillation policy identity mismatch');
  }
  const student = policy.students.find((entry) => entry.modelId === 'Qwen/Qwen3.5-0.8B');
  if (!student?.trainingSnapshotProvisioned) {
    throw new Error('0.8B student training snapshot is not admitted');
  }
  for (const arm of policy.arms) {
    const adapterRoot = path.resolve(arm.adapterPath);
    await Promise.all([
      fs.access(path.join(adapterRoot, 'adapter_config.json')),
      fs.access(path.join(adapterRoot, 'adapter_model.safetensors')),
    ]);
  }
  const role = corpusManifest.roles[args.role];
  if (!role?.taskManifestPath) throw new Error(`corpus role is unavailable: ${args.role}`);
  const [taskManifest, corpusPolicy, capabilityCatalog, formatCatalog] = await Promise.all([
    readJson(path.resolve(role.taskManifestPath)),
    readJson(path.resolve(corpusManifest.policy.path)),
    readJson(path.resolve(corpusManifest.capabilityCatalog.path)),
    readJson(path.join(ROOT, 'tools/data/wgsl-author-format-catalog.json')),
  ]);
  const families = new Map(capabilityCatalog.families.map((family) => [family.id, family]));
  const outputRoot = path.resolve(
    args.outputRoot
      || path.join(policy.artifactRoot, 'evaluation', args.role.replaceAll('_', '-'))
  );
  await fs.mkdir(outputRoot, { recursive: true });
  const referencePath = path.join(outputRoot, 'peft-reference.json');
  const reference = await runReference({
    outputPath: referencePath,
    modelPath: args.modelPath,
    datasetPath: role.datasetPath,
    student,
    policy,
    role: args.role,
    referenceBatchSize: args.referenceBatchSize,
  });
  if (
    reference.model?.revision !== student.revision
    || reference.model?.configSha256 !== student.configSha256
    || reference.model?.tokenizerSha256 !== student.tokenizerSha256
  ) {
    throw new Error('student PEFT reference model identity mismatch');
  }
  const runtime = corpusPolicy.runtime;
  const executor = await createWgslAuthorBrowserExecutor({
    browserArgs: runtime.browserArgs,
    headless: runtime.headless,
    requiredBackend: runtime.requiredBackend,
    requiredVendor: runtime.requiredVendor,
    requiredFeatures: runtime.requiredFeatures,
    requiredLimits: runtime.requiredLimits,
    powerPreference: runtime.powerPreference,
    executionTimeoutMs: runtime.executionTimeoutMs,
  });
  const candidates = [];
  let sessionCleanup = null;
  try {
    for (const candidate of reference.candidates) {
      const completionTasks = new Map(candidate.tasks.map((task) => [task.taskId, task]));
      const tasks = [];
      for (const task of taskManifest.tasks) {
        const completionTask = completionTasks.get(task.taskId);
        if (!completionTask) throw new Error(`${candidate.candidateId} is missing ${task.taskId}`);
        tasks.push(await evaluateCompletion({
          candidateId: candidate.candidateId,
          completion: candidate.completions[task.taskId],
          completionTask,
          outputTokenBudget: policy.evaluation.generation.maxNewTokens,
          task,
          family: families.get(task.semanticFamilyId),
          formatCatalog,
          runtime,
          executor,
        }));
      }
      candidates.push({
        candidateId: candidate.candidateId,
        adapterPath: candidate.adapterPath,
        adapterTreeSha256: candidate.adapterTreeSha256,
        tasks,
        summary: candidateSummary(tasks, candidate.tasks),
      });
    }
  } finally {
    sessionCleanup = await executor.close();
  }
  const core = {
    schema: 'doppler.wgsl-writer-family-distillation-evaluation/v1',
    policy: { path: path.relative(ROOT, POLICY_PATH), sha256: await sha256File(POLICY_PATH) },
    student,
    population: {
      role: args.role,
      path: role.taskManifestPath,
      sha256: await sha256File(path.resolve(role.taskManifestPath)),
      datasetPath: role.datasetPath,
      datasetSha256: role.datasetSha256,
      rows: role.rows,
    },
    reference: { path: referencePath, sha256: await sha256File(referencePath) },
    runtime: { identity: executor.runtimeIdentity, sessionCleanup },
    candidates,
    decision: 'evaluation_complete',
    comparisonAuthority: args.role === 'checkpoint_selection',
    generalWgslWriterClaim: false,
    promotionAuthority: false,
    claimBoundary: policy.claimBoundary,
  };
  const receipt = { ...core, receiptHash: hashWgslSemanticEvidenceValue(core) };
  const receiptPath = path.join(outputRoot, 'evaluation.json');
  await fs.writeFile(receiptPath, `${JSON.stringify(receipt, null, 2)}\n`, 'utf8');
  return { receiptPath, receipt };
}

async function main() {
  const result = await evaluateFamilyDistillation(parseArgs(process.argv.slice(2)));
  console.log(JSON.stringify({
    receiptPath: result.receiptPath,
    candidates: result.receipt.candidates.map((candidate) => ({
      candidateId: candidate.candidateId,
      summary: candidate.summary,
    })),
    receiptHash: result.receipt.receiptHash,
  }, null, 2));
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main().catch((error) => {
    console.error(error?.stack || error?.message || String(error));
    process.exitCode = 1;
  });
}

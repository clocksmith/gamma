#!/usr/bin/env node

import { createHash } from 'node:crypto';
import fs from 'node:fs/promises';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

import { hashWgslSemanticEvidenceValue } from '../src/tooling/wgsl-repair-semantic-gate.js';

const DEFAULT_POLICY = 'tools/policies/wgsl-writer-v2-training-policy.json';

function parseArgs(argv) {
  const args = { policyPath: DEFAULT_POLICY, evaluationRoot: '', outputPath: '' };
  for (let index = 0; index < argv.length; index += 1) {
    const token = argv[index];
    if (token === '--policy') args.policyPath = argv[++index] || '';
    else if (token === '--evaluation-root') args.evaluationRoot = argv[++index] || '';
    else if (token === '--out') args.outputPath = argv[++index] || '';
    else throw new Error(`Unknown argument: ${token}`);
  }
  return args;
}

async function readJson(filePath) {
  return JSON.parse(await fs.readFile(path.resolve(filePath), 'utf8'));
}

async function sha256File(filePath) {
  return createHash('sha256').update(await fs.readFile(path.resolve(filePath))).digest('hex');
}

function requireInternalHash(value, label) {
  const core = { ...value };
  const expected = core.receiptHash;
  delete core.receiptHash;
  if (expected !== hashWgslSemanticEvidenceValue(core)) {
    throw new Error(`${label} internal receipt hash mismatch.`);
  }
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
  throw new Error(`Writer seed selection is already sealed: ${filePath}`);
}

export function compareWriterCandidates(left, right) {
  const metricOrder = [
    ['semanticPassRate', -1],
    ['compilePassRate', -1],
    ['responseContractPassRate', -1],
    ['meanShaderCharacterCount', 1],
  ];
  for (const [field, direction] of metricOrder) {
    const delta = Number(left.summary[field]) - Number(right.summary[field]);
    if (delta !== 0) return delta * direction;
  }
  return left.seed - right.seed;
}

export function rankWriterCandidates(candidates) {
  return [...candidates].sort(compareWriterCandidates).map((entry, index) => ({
    ...entry,
    rank: index + 1,
  }));
}

async function loadCandidates(batch, policy) {
  const expectedSeeds = policy.workloads.map((entry) => entry.seed).sort((a, b) => a - b);
  const observedSeeds = batch.candidates.map((entry) => entry.seed).sort((a, b) => a - b);
  if (JSON.stringify(expectedSeeds) !== JSON.stringify(observedSeeds)) {
    throw new Error('Checkpoint selection requires every frozen seed exactly once.');
  }
  const candidates = [];
  for (const binding of batch.candidates) {
    await requireFileHash(binding.path, binding.sha256, `seed ${binding.seed} semantic receipt`);
    const receipt = await readJson(binding.path);
    requireInternalHash(receipt, `seed ${binding.seed} semantic receipt`);
    if (receipt.evaluationRole !== 'checkpoint_selection'
      || receipt.candidate?.seed !== binding.seed
      || receipt.submission?.ordinalForCandidate !== 1
      || receipt.selectionEvidence !== true) {
      throw new Error(`Seed ${binding.seed} checkpoint-selection evidence is invalid.`);
    }
    candidates.push({
      seed: binding.seed,
      summary: receipt.summary,
      adapterPath: receipt.candidate.adapterPath,
      adapterTreeSha256: receipt.candidate.adapterTreeSha256,
      trainingStatusPath: receipt.candidate.statusPath,
      trainingStatusSha256: receipt.candidate.statusSha256,
      semanticReceiptPath: binding.path,
      semanticReceiptSha256: binding.sha256,
      semanticReceiptHash: receipt.receiptHash,
    });
  }
  return candidates;
}

export async function selectWgslWriterV2Seed(args) {
  const policy = await readJson(args.policyPath);
  if (policy?.policyId !== 'doppler-wgsl-writer-v2-training') {
    throw new Error('WGSL writer selection requires the frozen writer-v2 policy.');
  }
  const evaluationRoot = path.resolve(
    args.evaluationRoot
      || path.join('reports/training/wgsl-writer', policy.experimentId, 'evaluation')
  );
  const batchPath = path.join(evaluationRoot, 'checkpoint-selection', 'evaluation.json');
  const outputPath = path.resolve(
    args.outputPath || path.join(evaluationRoot, 'selection', 'selected-seed.json')
  );
  await requireAbsent(outputPath);
  const batch = await readJson(batchPath);
  requireInternalHash(batch, 'checkpoint-selection batch');
  const policySha256 = await sha256File(args.policyPath);
  if (batch.decision !== 'evaluation_complete'
    || batch.selectionAuthority !== true
    || batch.policy?.sha256 !== policySha256) {
    throw new Error('Checkpoint-selection batch is not admitted by the frozen policy.');
  }
  const ranked = rankWriterCandidates(await loadCandidates(batch, policy));
  const selected = ranked[0];
  const core = {
    schema: 'doppler.wgsl-writer-seed-selection/v1',
    experimentId: policy.experimentId,
    policy: { path: args.policyPath, sha256: policySha256 },
    checkpointSelection: {
      path: path.relative(process.cwd(), batchPath),
      sha256: await sha256File(batchPath),
      receiptHash: batch.receiptHash,
    },
    metric: policy.evaluation.checkpointSelection.primaryMetric,
    tieBreakers: policy.evaluation.checkpointSelection.tieBreakers,
    rankedCandidates: ranked,
    selected: {
      seed: selected.seed,
      adapterPath: selected.adapterPath,
      adapterTreeSha256: selected.adapterTreeSha256,
      trainingStatusPath: selected.trainingStatusPath,
      trainingStatusSha256: selected.trainingStatusSha256,
    },
    decision: 'seed_selected',
    seedConfirmationSatisfied: false,
    dopplerParitySatisfied: false,
    promotionAuthority: false,
    generalWgslWriterClaim: false,
    claimBoundary: policy.claimBoundary,
  };
  const receipt = { ...core, receiptHash: hashWgslSemanticEvidenceValue(core) };
  await fs.mkdir(path.dirname(outputPath), { recursive: true });
  await fs.writeFile(outputPath, `${JSON.stringify(receipt, null, 2)}\n`, 'utf8');
  return { ok: true, outputPath, receipt };
}

async function main() {
  process.stdout.write(`${JSON.stringify(
    await selectWgslWriterV2Seed(parseArgs(process.argv.slice(2))),
    null,
    2
  )}\n`);
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main().catch((error) => {
    console.error(error instanceof Error ? error.stack : String(error));
    process.exitCode = 1;
  });
}

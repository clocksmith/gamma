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
  throw new Error(`Writer seed-confirmation decision is already sealed: ${filePath}`);
}

export function evaluateWriterSeedConfirmation(candidates, thresholds) {
  const confirmed = candidates.filter((entry) => (
    entry.semanticPassRate >= thresholds.minimumPerSeedSemanticPassRate
  ));
  const meanSemanticPassRate = candidates.reduce((sum, entry) => (
    sum + entry.semanticPassRate
  ), 0) / candidates.length;
  const checks = {
    minimumConfirmedSeeds: confirmed.length >= thresholds.minimumConfirmedSeeds,
    minimumMeanSemanticPassRate:
      meanSemanticPassRate >= thresholds.minimumMeanSemanticPassRate,
    minimumPerSeedSemanticPassRate: confirmed.length >= thresholds.minimumConfirmedSeeds,
    oneSubmissionPerCandidate: candidates.every((entry) => entry.submissionOrdinal === 1),
  };
  return {
    pass: Object.values(checks).every(Boolean),
    checks,
    confirmedSeeds: confirmed.map((entry) => entry.seed).sort((a, b) => a - b),
    confirmedSeedCount: confirmed.length,
    meanSemanticPassRate,
  };
}

async function loadCandidates(batch, policy) {
  const candidates = [];
  for (const binding of batch.candidates) {
    await requireFileHash(binding.path, binding.sha256, `seed ${binding.seed} confirmation receipt`);
    const receipt = await readJson(binding.path);
    requireInternalHash(receipt, `seed ${binding.seed} confirmation receipt`);
    if (receipt.evaluationRole !== 'seed_confirmation'
      || receipt.candidate?.seed !== binding.seed
      || receipt.confirmationEvidence !== true) {
      throw new Error(`Seed ${binding.seed} confirmation evidence is invalid.`);
    }
    candidates.push({
      seed: binding.seed,
      semanticPassRate: receipt.summary.semanticPassRate,
      semanticPasses: receipt.summary.semanticPasses,
      taskCount: receipt.summary.taskCount,
      compilePassRate: receipt.summary.compilePassRate,
      responseContractPassRate: receipt.summary.responseContractPassRate,
      submissionOrdinal: receipt.submission.ordinalForCandidate,
      semanticReceiptPath: binding.path,
      semanticReceiptSha256: binding.sha256,
      semanticReceiptHash: receipt.receiptHash,
    });
  }
  const expectedSeeds = policy.workloads.map((entry) => entry.seed).sort((a, b) => a - b);
  const observedSeeds = candidates.map((entry) => entry.seed).sort((a, b) => a - b);
  if (JSON.stringify(expectedSeeds) !== JSON.stringify(observedSeeds)) {
    throw new Error('Seed confirmation requires every frozen seed exactly once.');
  }
  return candidates.sort((left, right) => left.seed - right.seed);
}

export async function finalizeWgslWriterV2Confirmation(args) {
  const policy = await readJson(args.policyPath);
  if (policy?.policyId !== 'doppler-wgsl-writer-v2-training') {
    throw new Error('WGSL writer confirmation requires the frozen writer-v2 policy.');
  }
  const evaluationRoot = path.resolve(
    args.evaluationRoot
      || path.join('reports/training/wgsl-writer', policy.experimentId, 'evaluation')
  );
  const selectionPath = path.join(evaluationRoot, 'selection', 'selected-seed.json');
  const batchPath = path.join(evaluationRoot, 'seed-confirmation', 'evaluation.json');
  const outputPath = path.resolve(args.outputPath || path.join(evaluationRoot, 'confirmation.json'));
  await requireAbsent(outputPath);
  const [selection, batch] = await Promise.all([
    readJson(selectionPath),
    readJson(batchPath),
  ]);
  requireInternalHash(selection, 'writer seed selection');
  requireInternalHash(batch, 'seed-confirmation batch');
  const policySha256 = await sha256File(args.policyPath);
  if (selection.decision !== 'seed_selected'
    || batch.decision !== 'evaluation_complete'
    || batch.confirmationAuthority !== true
    || selection.policy?.sha256 !== policySha256
    || batch.policy?.sha256 !== policySha256) {
    throw new Error('Writer seed-confirmation inputs are not admitted by the frozen policy.');
  }
  const candidates = await loadCandidates(batch, policy);
  const thresholds = policy.evaluation.seedConfirmation;
  const result = evaluateWriterSeedConfirmation(candidates, thresholds);
  const selectedConfirmed = result.confirmedSeeds.includes(selection.selected.seed);
  const pass = result.pass && selectedConfirmed;
  const core = {
    schema: 'doppler.wgsl-writer-seed-confirmation/v1',
    experimentId: policy.experimentId,
    policy: { path: args.policyPath, sha256: policySha256 },
    selection: {
      path: path.relative(process.cwd(), selectionPath),
      sha256: await sha256File(selectionPath),
      receiptHash: selection.receiptHash,
      selectedSeed: selection.selected.seed,
    },
    confirmationBatch: {
      path: path.relative(process.cwd(), batchPath),
      sha256: await sha256File(batchPath),
      receiptHash: batch.receiptHash,
    },
    thresholds: {
      minimumConfirmedSeeds: thresholds.minimumConfirmedSeeds,
      minimumMeanSemanticPassRate: thresholds.minimumMeanSemanticPassRate,
      minimumPerSeedSemanticPassRate: thresholds.minimumPerSeedSemanticPassRate,
      submissionsPerCandidate: thresholds.submissionsPerCandidate,
    },
    candidates,
    result: { ...result, selectedSeedConfirmed: selectedConfirmed },
    decision: pass ? 'seed_confirmation_passed' : 'seed_confirmation_failed',
    selectedAdapter: selection.selected,
    dopplerParitySatisfied: false,
    promotionAuthority: false,
    generalWgslWriterClaim: false,
    claimBoundary: policy.claimBoundary,
  };
  const receipt = { ...core, receiptHash: hashWgslSemanticEvidenceValue(core) };
  await fs.mkdir(path.dirname(outputPath), { recursive: true });
  await fs.writeFile(outputPath, `${JSON.stringify(receipt, null, 2)}\n`, 'utf8');
  return { ok: pass, outputPath, receipt };
}

async function main() {
  const result = await finalizeWgslWriterV2Confirmation(parseArgs(process.argv.slice(2)));
  process.stdout.write(`${JSON.stringify(result, null, 2)}\n`);
  if (!result.ok) process.exitCode = 1;
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main().catch((error) => {
    console.error(error instanceof Error ? error.stack : String(error));
    process.exitCode = 1;
  });
}

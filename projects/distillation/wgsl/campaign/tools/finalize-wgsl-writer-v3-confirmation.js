#!/usr/bin/env node

import { createHash } from 'node:crypto';
import fs from 'node:fs/promises';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

import { hashWgslSemanticEvidenceValue } from '../src/tooling/wgsl-repair-semantic-gate.js';

const POLICY_PATH = 'tools/policies/wgsl-writer-v3-training-policy.json';
const SELECTION_PATH =
  'reports/training/wgsl-writer/doppler-wgsl-writer-v3/evaluation/selection/selected-lane.json';
const EVALUATION_PATH =
  'reports/training/wgsl-writer/doppler-wgsl-writer-v3/evaluation/seed-confirmation/evaluation.json';
const OUTPUT_PATH =
  'reports/training/wgsl-writer/doppler-wgsl-writer-v3/evaluation/confirmation/confirmation.json';

function parseArgs(argv) {
  const args = {
    policyPath: POLICY_PATH,
    selectionPath: '',
    evaluationPath: '',
    outputPath: '',
  };
  for (let index = 0; index < argv.length; index += 1) {
    const token = argv[index];
    if (token === '--policy') args.policyPath = argv[++index] || '';
    else if (token === '--selection') args.selectionPath = argv[++index] || '';
    else if (token === '--evaluation') args.evaluationPath = argv[++index] || '';
    else if (token === '--out') args.outputPath = argv[++index] || '';
    else throw new Error(`Unknown argument: ${token}`);
  }
  if (!args.policyPath) throw new Error('--policy requires a value.');
  return args;
}

async function readJson(filePath) {
  return JSON.parse(await fs.readFile(filePath, 'utf8'));
}

async function sha256File(filePath) {
  return createHash('sha256').update(await fs.readFile(filePath)).digest('hex');
}

export async function finalizeWgslWriterV3Confirmation(options = {}) {
  const policyPath = options.policyPath || POLICY_PATH;
  const policy = await readJson(policyPath);
  const selectionPath = options.selectionPath
    || policy.evaluation.selectionReceiptPath
    || SELECTION_PATH;
  const evaluationPath = options.evaluationPath || path.join(
    policy.artifactRoot || 'reports/training/wgsl-writer/doppler-wgsl-writer-v3',
    'evaluation',
    'seed-confirmation',
    'evaluation.json'
  );
  const outputPath = options.outputPath || path.join(
    policy.artifactRoot || path.dirname(path.dirname(path.dirname(OUTPUT_PATH))),
    'evaluation',
    'confirmation',
    'confirmation.json'
  );
  const [selection, evaluation] = await Promise.all([
    readJson(selectionPath),
    readJson(evaluationPath),
  ]);
  if (selection.decision !== 'lane_selected') {
    throw new Error('WGSL writer v3 confirmation requires a selected lane.');
  }
  if (!Array.isArray(evaluation.candidates)) {
    throw new Error('WGSL writer v3 confirmation candidates must be an array.');
  }
  const candidates = evaluation.candidates.filter((candidate) => (
    candidate.capabilityAuthority === true
  ));
  const expectedSeeds = policy.evaluation.confirmationSeeds;
  if (candidates.length !== expectedSeeds.length) {
    throw new Error('WGSL writer v3 confirmation candidate count mismatch.');
  }
  const rates = candidates.map((candidate) => candidate.summary.semanticPassRate);
  if (rates.some((rate) => !Number.isFinite(rate) || rate < 0 || rate > 1)) {
    throw new Error('WGSL writer v3 confirmation halted on a nonfinite or out-of-range semantic pass rate.');
  }
  const thresholds = [
    policy.evaluation.minimumConfirmationPerSeedSemanticPassRate,
    policy.evaluation.minimumConfirmationMeanSemanticPassRate,
  ];
  if (thresholds.some((threshold) => !Number.isFinite(threshold) || threshold < 0 || threshold > 1)) {
    throw new Error('WGSL writer v3 confirmation halted on a nonfinite or out-of-range threshold.');
  }
  const mean = rates.reduce((sum, value) => sum + value, 0) / rates.length;
  const perSeedPass = rates.every((rate) => (
    rate >= policy.evaluation.minimumConfirmationPerSeedSemanticPassRate
  ));
  const meanPass = mean >= policy.evaluation.minimumConfirmationMeanSemanticPassRate;
  const confirmed = perSeedPass && meanPass;
  const core = {
    schema: 'doppler.wgsl-writer-v3-confirmation/v1',
    experimentId: policy.experimentId,
    policy: { path: policyPath, sha256: await sha256File(policyPath) },
    selection: { path: selectionPath, sha256: await sha256File(selectionPath) },
    evaluation: { path: evaluationPath, sha256: await sha256File(evaluationPath) },
    selectedLaneId: selection.selected.candidateId,
    candidates: candidates.map((candidate) => ({
      candidateId: candidate.candidateId,
      adapterPath: candidate.adapterPath,
      adapterTreeSha256: candidate.adapterTreeSha256,
      semanticPassRate: candidate.summary.semanticPassRate,
    })),
    thresholds: {
      minimumPerSeedSemanticPassRate: policy.evaluation.minimumConfirmationPerSeedSemanticPassRate,
      minimumMeanSemanticPassRate: policy.evaluation.minimumConfirmationMeanSemanticPassRate,
    },
    meanSemanticPassRate: mean,
    decision: confirmed ? 'lane_seed_confirmed' : 'lane_seed_confirmation_failed',
    dopplerParityAuthority: confirmed,
    promotionAuthority: false,
    generalWgslWriterClaim: false,
    claimBoundary: policy.claimBoundary,
  };
  const receipt = { ...core, receiptHash: hashWgslSemanticEvidenceValue(core) };
  await fs.mkdir(path.dirname(outputPath), { recursive: true });
  await fs.writeFile(outputPath, `${JSON.stringify(receipt, null, 2)}\n`, 'utf8');
  return { outputPath, receipt };
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  finalizeWgslWriterV3Confirmation(parseArgs(process.argv.slice(2))).then((result) => {
    process.stdout.write(`${JSON.stringify(result, null, 2)}\n`);
    if (!result.receipt.dopplerParityAuthority) process.exitCode = 1;
  }).catch((error) => {
    console.error(error instanceof Error ? error.stack : String(error));
    process.exitCode = 1;
  });
}

#!/usr/bin/env node

import { createHash } from 'node:crypto';
import fs from 'node:fs/promises';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

import { hashWgslSemanticEvidenceValue } from '../src/tooling/wgsl-repair-semantic-gate.js';

const POLICY_PATH = 'tools/policies/wgsl-writer-v3-training-policy.json';
const EVALUATION_PATH =
  'reports/training/wgsl-writer/doppler-wgsl-writer-v3/evaluation/checkpoint-selection/evaluation.json';
const OUTPUT_PATH =
  'reports/training/wgsl-writer/doppler-wgsl-writer-v3/evaluation/selection/selected-lane.json';

function parseArgs(argv) {
  const args = { policyPath: POLICY_PATH, evaluationPath: EVALUATION_PATH, outputPath: '' };
  for (let index = 0; index < argv.length; index += 1) {
    const token = argv[index];
    if (token === '--policy') args.policyPath = argv[++index] || '';
    else if (token === '--evaluation') args.evaluationPath = argv[++index] || '';
    else if (token === '--out') args.outputPath = argv[++index] || '';
    else throw new Error(`Unknown argument: ${token}`);
  }
  if (!args.policyPath || !args.evaluationPath) {
    throw new Error('--policy and --evaluation require values.');
  }
  return args;
}

async function readJson(filePath) {
  return JSON.parse(await fs.readFile(filePath, 'utf8'));
}

async function sha256File(filePath) {
  return createHash('sha256').update(await fs.readFile(filePath)).digest('hex');
}

function compare(left, right) {
  const fields = [
    'semanticPassRate',
    'qualityPasses',
    'responseContractPasses',
    'compilePasses',
  ];
  for (const field of fields) {
    if (left.summary[field] !== right.summary[field]) {
      return right.summary[field] - left.summary[field];
    }
  }
  if (left.summary.meanResponseCharacters !== right.summary.meanResponseCharacters) {
    return left.summary.meanResponseCharacters - right.summary.meanResponseCharacters;
  }
  return left.candidateId.localeCompare(right.candidateId);
}

export async function selectWgslWriterV3Lane(options = {}) {
  const policyPath = options.policyPath || POLICY_PATH;
  const evaluationPath = options.evaluationPath || EVALUATION_PATH;
  const policy = await readJson(policyPath);
  const evaluation = await readJson(evaluationPath);
  const outputPath = options.outputPath
    || policy.evaluation.selectionReceiptPath
    || OUTPUT_PATH;
  const candidates = evaluation.candidates
    .filter((candidate) => candidate.capabilityAuthority === true)
    .sort(compare);
  if (candidates.length === 0) throw new Error('No authoritative V3 candidate was evaluated.');
  const selected = candidates[0];
  const admitted = selected.summary.semanticPassRate
    >= policy.evaluation.minimumSelectionSemanticPassRate;
  const core = {
    schema: 'doppler.wgsl-writer-v3-lane-selection/v1',
    experimentId: policy.experimentId,
    policy: { path: policyPath, sha256: await sha256File(policyPath) },
    evaluation: { path: evaluationPath, sha256: await sha256File(evaluationPath) },
    ranking: candidates.map((candidate, index) => ({
      rank: index + 1,
      candidateId: candidate.candidateId,
      summary: candidate.summary,
    })),
    selected: admitted ? {
      candidateId: selected.candidateId,
      adapterPath: selected.adapterPath,
      adapterTreeSha256: selected.adapterTreeSha256,
      summary: selected.summary,
    } : null,
    minimumSemanticPassRate: policy.evaluation.minimumSelectionSemanticPassRate,
    decision: admitted ? 'lane_selected' : 'no_lane_met_selection_gate',
    seedConfirmationAuthority: admitted,
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
  selectWgslWriterV3Lane(parseArgs(process.argv.slice(2))).then((result) => {
    process.stdout.write(`${JSON.stringify(result, null, 2)}\n`);
    if (!result.receipt.seedConfirmationAuthority) process.exitCode = 1;
  }).catch((error) => {
    console.error(error instanceof Error ? error.stack : String(error));
    process.exitCode = 1;
  });
}

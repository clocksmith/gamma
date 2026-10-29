#!/usr/bin/env node

import { createHash } from 'node:crypto';
import fs from 'node:fs/promises';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

import { hashWgslSemanticEvidenceValue } from '../src/tooling/wgsl-repair-semantic-gate.js';

const DEFAULT_POLICY = 'tools/policies/wgsl-repair-v13-seed-selection-policy.json';

function parseArgs(argv) {
  const args = { policyPath: DEFAULT_POLICY, receiptPaths: [] };
  for (let index = 0; index < argv.length; index += 1) {
    const token = argv[index];
    if (token === '--policy') args.policyPath = argv[++index] || '';
    else if (token === '--receipt') args.receiptPaths.push(argv[++index] || '');
    else throw new Error(`Unknown argument: ${token}`);
  }
  if (args.receiptPaths.length !== 3) {
    throw new Error('Exactly three --receipt paths are required.');
  }
  return args;
}

async function readJson(filePath) {
  return JSON.parse(await fs.readFile(path.resolve(filePath), 'utf8'));
}

async function sha256File(filePath) {
  const bytes = await fs.readFile(path.resolve(filePath));
  return createHash('sha256').update(bytes).digest('hex');
}

function scoreReceipt(receipt) {
  const tasks = Array.isArray(receipt.tasks) ? receipt.tasks : [];
  const evaluatedTasks = Array.isArray(receipt.evaluatedTasks) ? receipt.evaluatedTasks : [];
  return {
    semanticTaskPassCount: evaluatedTasks.filter((task) => task.pass === true).length,
    compilePassCount: tasks.filter((task) => task.compilation?.status === 'pass').length,
    semanticVariantPassCount: evaluatedTasks.reduce((sum, task) => (
      sum + (task.variants || []).filter((variant) => (
        variant.dispatchPass === true
        && variant.numeric?.pass === true
        && variant.hashBindingPass === true
        && variant.boundsPass === true
      )).length
    ), 0),
    exactReferenceCompletionCount: tasks.filter((task) => (
      task.exactReferenceCompletion === true
    )).length,
  };
}

function compareRanked(left, right) {
  const fields = [
    'semanticTaskPassCount',
    'compilePassCount',
    'semanticVariantPassCount',
    'exactReferenceCompletionCount',
  ];
  for (const field of fields) {
    if (left.score[field] !== right.score[field]) {
      return right.score[field] - left.score[field];
    }
  }
  return left.seed - right.seed;
}

function validateReceipt(policy, receipt) {
  if (receipt?.schema !== 'doppler.wgsl-repair-semantic-dispatch-receipt/v1'
    || receipt?.experimentId !== 'doppler-wgsl-repair-v13'
    || receipt?.mode !== 'candidate'
    || receipt?.evaluationRole !== 'checkpoint_selection'
    || receipt?.taskManifest?.path !== policy.populations.checkpointSelection.path
    || receipt?.taskManifest?.sha256 !== policy.populations.checkpointSelection.sha256) {
    throw new Error('Candidate semantic receipt does not match the frozen selection population.');
  }
  const seed = receipt.candidate?.seed;
  const eligible = policy.eligibleCandidates.find((entry) => entry.seed === seed);
  if (!eligible
    || receipt.candidate.adapterManifestSha256 !== eligible.adapterManifestSha256
    || receipt.candidate.adapterWeightsSha256 !== eligible.adapterWeightsSha256) {
    throw new Error(`Candidate semantic receipt has invalid seed or adapter identity: ${seed}.`);
  }
  if (!receipt.candidateCompletions?.path
    || !receipt.candidateCompletions?.sha256
    || !receipt.candidateCompletions?.receiptHash) {
    throw new Error(`Candidate semantic receipt is missing completion binding: ${seed}.`);
  }
  const receiptCore = { ...receipt };
  delete receiptCore.receiptHash;
  if (receipt.receiptHash !== hashWgslSemanticEvidenceValue(receiptCore)) {
    throw new Error(`Candidate semantic receipt hash failed for seed ${seed}.`);
  }
  return eligible;
}

export async function selectWgslRepairV13Seed(args) {
  const policy = await readJson(args.policyPath);
  const policySha256 = await sha256File(args.policyPath);
  const receipts = [];
  for (const receiptPath of args.receiptPaths) {
    const receipt = await readJson(receiptPath);
    const eligible = validateReceipt(policy, receipt);
    const completionDocument = await readJson(receipt.candidateCompletions.path);
    const completionSha256 = await sha256File(receipt.candidateCompletions.path);
    const completionCore = { ...completionDocument };
    delete completionCore.receiptHash;
    if (completionSha256 !== receipt.candidateCompletions.sha256
      || completionDocument.receiptHash !== receipt.candidateCompletions.receiptHash
      || completionDocument.receiptHash !== hashWgslSemanticEvidenceValue(completionCore)
      || completionDocument.candidate?.seed !== eligible.seed
      || completionDocument.population?.sha256 !== policy.populations.checkpointSelection.sha256) {
      throw new Error(`Candidate completion binding failed for seed ${eligible.seed}.`);
    }
    receipts.push({
      seed: eligible.seed,
      eligible,
      receiptPath,
      receiptSha256: await sha256File(receiptPath),
      receiptHash: receipt.receiptHash,
      completionBinding: receipt.candidateCompletions,
      score: scoreReceipt(receipt),
      decision: receipt.decision,
    });
  }
  const seeds = new Set(receipts.map((entry) => entry.seed));
  if (seeds.size !== policy.eligibleCandidates.length) {
    throw new Error('Candidate receipts must cover seeds 11, 29, and 47 exactly once.');
  }
  const ranked = [...receipts].sort(compareRanked);
  const selected = ranked[0];
  const core = {
    schema: 'doppler.wgsl-repair-v13-seed-selection/v1',
    experimentId: 'doppler-wgsl-repair-v13',
    policy: { path: args.policyPath, sha256: policySha256 },
    population: policy.populations.checkpointSelection,
    ranking: policy.ranking,
    rankedCandidates: ranked.map((entry, index) => ({
      rank: index + 1,
      seed: entry.seed,
      adapterManifestSha256: entry.eligible.adapterManifestSha256,
      adapterWeightsSha256: entry.eligible.adapterWeightsSha256,
      semanticReceiptPath: entry.receiptPath,
      semanticReceiptSha256: entry.receiptSha256,
      semanticReceiptHash: entry.receiptHash,
      candidateCompletions: entry.completionBinding,
      semanticDecision: entry.decision,
      score: entry.score,
    })),
    selected: {
      lane: policy.eligibleLane,
      seed: selected.seed,
      adapterPath: selected.eligible.adapterWeightsPath,
      adapterSha256: selected.eligible.adapterWeightsSha256,
      adapterManifestPath: selected.eligible.adapterManifestPath,
      adapterManifestSha256: selected.eligible.adapterManifestSha256,
    },
    decision: 'selected_for_seed_confirmation',
    selectionAuthority: true,
    seedConfirmationSatisfied: false,
    promotionAuthority: false,
    claimBoundary: policy.claimBoundary,
  };
  return { ...core, receiptHash: hashWgslSemanticEvidenceValue(core) };
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const receipt = await selectWgslRepairV13Seed(args);
  process.stdout.write(`${JSON.stringify(receipt, null, 2)}\n`);
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main().catch((error) => {
    console.error(error instanceof Error ? error.stack : String(error));
    process.exitCode = 1;
  });
}

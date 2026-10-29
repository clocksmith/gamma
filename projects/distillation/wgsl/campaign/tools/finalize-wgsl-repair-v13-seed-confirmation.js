#!/usr/bin/env node

import { createHash } from 'node:crypto';
import fs from 'node:fs/promises';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

import { hashWgslSemanticEvidenceValue } from '../src/tooling/wgsl-repair-semantic-gate.js';

const DEFAULT_POLICY = 'tools/policies/wgsl-repair-v13-seed-confirmation-policy.json';
const DEFAULT_REFERENCE = 'docs/status/wgsl-repair-v13-seed-confirmation-reference-2026-07-14.json';
const DEFAULT_COMPLETIONS = 'reports/training/wgsl-repair/doppler-wgsl-repair-v13/seed-confirmation/seed29.completions.json';
const DEFAULT_SEMANTIC = 'reports/training/wgsl-repair/doppler-wgsl-repair-v13/seed-confirmation/seed29.semantic.json';

function parseArgs(argv) {
  const args = {
    policyPath: DEFAULT_POLICY,
    referencePath: DEFAULT_REFERENCE,
    completionsPath: DEFAULT_COMPLETIONS,
    semanticPath: DEFAULT_SEMANTIC,
    outputPath: '',
  };
  for (let index = 0; index < argv.length; index += 1) {
    const token = argv[index];
    if (token === '--policy') args.policyPath = argv[++index] || '';
    else if (token === '--reference') args.referencePath = argv[++index] || '';
    else if (token === '--completions') args.completionsPath = argv[++index] || '';
    else if (token === '--semantic') args.semanticPath = argv[++index] || '';
    else if (token === '--out') args.outputPath = argv[++index] || '';
    else throw new Error(`Unknown argument: ${token}`);
  }
  if (!args.outputPath) throw new Error('--out is required.');
  return args;
}

async function readJson(filePath) {
  return JSON.parse(await fs.readFile(path.resolve(filePath), 'utf8'));
}

async function sha256File(filePath) {
  const bytes = await fs.readFile(path.resolve(filePath));
  return createHash('sha256').update(bytes).digest('hex');
}

function requireInternalReceiptHash(receipt, label) {
  const core = { ...receipt };
  delete core.receiptHash;
  const expected = hashWgslSemanticEvidenceValue(core);
  if (receipt?.receiptHash !== expected) {
    throw new Error(`${label} internal receipt hash mismatch.`);
  }
}

async function requireFileHash(filePath, expectedSha256, label) {
  const actual = await sha256File(filePath);
  if (actual !== expectedSha256) {
    throw new Error(`${label} SHA-256 mismatch: expected ${expectedSha256}, got ${actual}.`);
  }
  return actual;
}

export async function finalizeWgslRepairV13SeedConfirmation(args) {
  const [policy, reference, completions, semantic] = await Promise.all([
    readJson(args.policyPath),
    readJson(args.referencePath),
    readJson(args.completionsPath),
    readJson(args.semanticPath),
  ]);
  const portability = await readJson(policy.predecessor.adapterPortabilityReceiptPath);
  const preservation = await readJson(portability.preservation.receiptPath);
  requireInternalReceiptHash(reference, 'reference receipt');
  requireInternalReceiptHash(completions, 'completion receipt');
  requireInternalReceiptHash(semantic, 'semantic receipt');
  requireInternalReceiptHash(portability, 'adapter-portability receipt');
  requireInternalReceiptHash(preservation, 'adapter-preservation receipt');
  const [
    policySha256,
    referenceSha256,
    completionsSha256,
    semanticSha256,
  ] = await Promise.all([
    sha256File(args.policyPath),
    sha256File(args.referencePath),
    sha256File(args.completionsPath),
    sha256File(args.semanticPath),
    requireFileHash(
      policy.populations.seedConfirmation.path,
      policy.populations.seedConfirmation.sha256,
      'seed-confirmation population'
    ),
    requireFileHash(
      policy.selectionReceipt.path,
      policy.selectionReceipt.sha256,
      'seed-selection receipt'
    ),
    requireFileHash(
      policy.eligibleCandidates[0].adapterManifestPath,
      policy.eligibleCandidates[0].adapterManifestSha256,
      'seed-29 adapter manifest'
    ),
    requireFileHash(
      policy.predecessor.adapterPortabilityReceiptPath,
      policy.predecessor.adapterPortabilityReceiptSha256,
      'adapter-portability receipt'
    ),
    requireFileHash(
      portability.preservation.receiptPath,
      portability.preservation.receiptSha256,
      'adapter-preservation receipt'
    ),
  ]);
  const candidate = policy.eligibleCandidates[0];
  const preservedCandidate = preservation.artifacts?.find((entry) => entry.seed === candidate.seed);
  if (portability.frozenParityGate?.decision !== policy.predecessor.requiredDecision
    || portability.preservation?.decision !== 'complete'
    || preservation.decision !== 'complete'
    || preservation.externallyPreserved !== true
    || preservedCandidate?.adapter?.ok !== true
    || preservedCandidate?.adapter?.expectedSha256 !== candidate.adapterWeightsSha256
    || preservedCandidate?.adapter?.observedSha256 !== candidate.adapterWeightsSha256
    || preservedCandidate?.externalVerification?.ok !== true
    || preservedCandidate?.externalVerification?.observedSha256
      !== candidate.adapterWeightsSha256) {
    throw new Error('Seed-confirmation adapter preservation binding failed.');
  }
  if (candidate.seed !== 29
    || completions.candidate?.seed !== 29
    || semantic.candidate?.seed !== 29
    || completions.population?.sha256 !== policy.populations.seedConfirmation.sha256
    || semantic.taskManifest?.sha256 !== policy.populations.seedConfirmation.sha256
    || completions.policy?.sha256 !== policySha256
    || semantic.candidateCompletions?.sha256 !== completionsSha256
    || semantic.candidateCompletions?.receiptHash !== completions.receiptHash) {
    throw new Error('Seed-confirmation candidate or population binding failed.');
  }
  if (reference.mode !== 'reference'
    || reference.decision !== 'reference_mechanics_passed'
    || reference.taskManifest?.sha256 !== policy.populations.seedConfirmation.sha256
    || !reference.evaluatedTasks?.every((task) => task.pass === true)) {
    throw new Error('Reference qualification binding failed.');
  }
  const summary = semantic.summary || {};
  const decisionRule = policy.decisionRule;
  const semanticTaskPasses = (semantic.evaluatedTasks || [])
    .filter((task) => task.pass === true).length;
  const exactReferenceCompletionCount = (semantic.tasks || [])
    .filter((task) => task.exactReferenceCompletion === true).length;
  const checks = {
    submissionCount: decisionRule.submissionCount === 1,
    candidateIdentity: semantic.candidate?.adapterWeightsSha256 === candidate.adapterWeightsSha256,
    responseContractPasses: summary.responseContractPasses
      === decisionRule.requiredResponseContractPasses,
    compilationPasses: summary.compilationPasses === decisionRule.requiredCompilationPasses,
    semanticTaskPasses: semanticTaskPasses === decisionRule.requiredSemanticTaskPasses,
    semanticVariantPasses: summary.dispatchVariantPasses
      === decisionRule.requiredSemanticVariantPasses,
    historicalRegressionPasses: summary.historicalRegressionPasses
      === decisionRule.requiredHistoricalRegressionPasses,
    semanticReceiptDecision: semantic.decision === 'candidate_tasks_passed',
  };
  const pass = Object.values(checks).every(Boolean);
  const core = {
    schema: 'doppler.wgsl-repair-v13-seed-confirmation-result/v1',
    experimentId: 'doppler-wgsl-repair-v13',
    policy: { path: args.policyPath, sha256: policySha256 },
    population: policy.populations.seedConfirmation,
    selectionReceipt: policy.selectionReceipt,
    candidate: {
      lane: policy.eligibleLane,
      seed: candidate.seed,
      adapterManifestPath: candidate.adapterManifestPath,
      adapterManifestSha256: candidate.adapterManifestSha256,
      adapterWeightsPath: candidate.adapterWeightsPath,
      adapterWeightsSha256: candidate.adapterWeightsSha256,
    },
    referenceReceipt: {
      path: args.referencePath,
      sha256: referenceSha256,
      receiptHash: reference.receiptHash,
      decision: reference.decision,
    },
    completionReceipt: {
      path: args.completionsPath,
      sha256: completionsSha256,
      receiptHash: completions.receiptHash,
    },
    semanticReceipt: {
      path: args.semanticPath,
      sha256: semanticSha256,
      receiptHash: semantic.receiptHash,
      decision: semantic.decision,
    },
    oneUseSubmission: {
      submissionOrdinal: 1,
      committedPolicySubmissionCount: decisionRule.submissionCount,
      retryPerformed: false,
      promptOrSamplerChangedAfterFreeze: false,
    },
    metrics: {
      taskCount: summary.taskCount,
      responseContractPasses: summary.responseContractPasses,
      compilationPasses: summary.compilationPasses,
      semanticTaskPasses,
      semanticVariantCount: summary.dispatchVariantCount,
      semanticVariantPasses: summary.dispatchVariantPasses,
      historicalRegressionPasses: summary.historicalRegressionPasses,
      exactReferenceCompletionCount,
    },
    checks,
    decision: pass ? decisionRule.passDecision : decisionRule.failureDecision,
    seedConfirmationSatisfied: pass,
    promotionAuthority: false,
    wgslDoctorAllowed: false,
    completeShaderWritingEstablished: false,
    claimBoundary: pass
      ? 'Seed 29 passed one commit-derived, disjoint, constructed replacement-only semantic WGSL confirmation population under the frozen F16 Doppler artifact and sampler. This is seed-confirmed repair evidence, not promotion, natural-error evidence, WGSL Doctor authorization, or complete shader writing.'
      : 'Seed 29 failed the frozen semantic confirmation policy. V13 promotion, WGSL Doctor, and complete shader writing remain rejected.',
  };
  return { ...core, receiptHash: hashWgslSemanticEvidenceValue(core) };
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const receipt = await finalizeWgslRepairV13SeedConfirmation(args);
  const outputPath = path.resolve(args.outputPath);
  await fs.mkdir(path.dirname(outputPath), { recursive: true });
  await fs.writeFile(outputPath, `${JSON.stringify(receipt, null, 2)}\n`, 'utf8');
  console.error(`[wgsl-seed-confirmation] wrote ${args.outputPath}`);
  if (!receipt.seedConfirmationSatisfied) process.exitCode = 1;
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main().catch((error) => {
    console.error(error instanceof Error ? error.stack : String(error));
    process.exitCode = 1;
  });
}

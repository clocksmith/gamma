#!/usr/bin/env node

import { createHash } from 'node:crypto';
import fs from 'node:fs/promises';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

import { hashWgslSemanticEvidenceValue } from '../src/tooling/wgsl-repair-semantic-gate.js';

const DEFAULT_POLICY = 'tools/policies/wgsl-writer-v1-diagnostic-policy.json';
const DEFAULT_BASE_COMPLETIONS =
  'reports/training/wgsl-writer/doppler-wgsl-writer-v1/diagnostic/base.completions.json';
const DEFAULT_BASE_SEMANTIC =
  'reports/training/wgsl-writer/doppler-wgsl-writer-v1/diagnostic/base.semantic.json';
const DEFAULT_ADAPTER_COMPLETIONS =
  'reports/training/wgsl-writer/doppler-wgsl-writer-v1/diagnostic/seed29.completions.json';
const DEFAULT_ADAPTER_SEMANTIC =
  'reports/training/wgsl-writer/doppler-wgsl-writer-v1/diagnostic/seed29.semantic.json';

function parseArgs(argv) {
  const args = {
    policyPath: DEFAULT_POLICY,
    baseCompletionsPath: DEFAULT_BASE_COMPLETIONS,
    baseSemanticPath: DEFAULT_BASE_SEMANTIC,
    adapterCompletionsPath: DEFAULT_ADAPTER_COMPLETIONS,
    adapterSemanticPath: DEFAULT_ADAPTER_SEMANTIC,
    outputPath: '',
  };
  for (let index = 0; index < argv.length; index += 1) {
    const token = argv[index];
    if (token === '--policy') args.policyPath = argv[++index] || '';
    else if (token === '--base-completions') args.baseCompletionsPath = argv[++index] || '';
    else if (token === '--base-semantic') args.baseSemanticPath = argv[++index] || '';
    else if (token === '--adapter-completions') {
      args.adapterCompletionsPath = argv[++index] || '';
    } else if (token === '--adapter-semantic') {
      args.adapterSemanticPath = argv[++index] || '';
    } else if (token === '--out') args.outputPath = argv[++index] || '';
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

async function requireFileHash(filePath, expectedSha256, label) {
  const actual = await sha256File(filePath);
  if (actual !== expectedSha256) {
    throw new Error(`${label} SHA-256 mismatch: expected ${expectedSha256}, got ${actual}.`);
  }
  return actual;
}

function requireInternalReceiptHash(receipt, label) {
  const core = { ...receipt };
  delete core.receiptHash;
  if (receipt?.receiptHash !== hashWgslSemanticEvidenceValue(core)) {
    throw new Error(`${label} internal receipt hash mismatch.`);
  }
}

function stableEqual(left, right) {
  return hashWgslSemanticEvidenceValue(left) === hashWgslSemanticEvidenceValue(right);
}

function summarizeLane(completions, semantic, paths, hashes) {
  const taskCount = semantic.summary?.taskCount || 0;
  const semanticTaskPasses = semantic.summary?.semanticTaskPasses || 0;
  const responseContractPasses = semantic.summary?.responseContractPasses || 0;
  const compilationPasses = semantic.summary?.compilationPasses || 0;
  return {
    candidateId: completions.candidate.id,
    candidateKind: completions.candidate.kind,
    completionReceipt: {
      path: paths.completions,
      sha256: hashes.completions,
      receiptHash: completions.receiptHash,
    },
    semanticReceipt: {
      path: paths.semantic,
      sha256: hashes.semantic,
      receiptHash: semantic.receiptHash,
      decision: semantic.decision,
    },
    metrics: {
      taskCount,
      responseContractPasses,
      compilationPasses,
      semanticTaskPasses,
      dispatchVariantPasses: semantic.summary?.dispatchVariantPasses || 0,
      historicalRegressionPasses: semantic.summary?.historicalRegressionPasses || 0,
      exactReferenceCompletions: completions.tasks.filter((task) => (
        task.exactReferenceCompletion === true
      )).length,
      maxTokenCapHits: completions.tasks.filter((task) => (
        task.generation?.tokenIds?.length === completions.generation.maxTokens
      )).length,
    },
    taskOutcomes: semantic.evaluatedTasks.map((task) => ({
      taskId: task.taskId,
      pass: task.pass,
      blockers: task.blockers,
    })),
    completeVisibleMechanicsPass: taskCount > 0
      && responseContractPasses === taskCount
      && compilationPasses === taskCount
      && semanticTaskPasses === taskCount,
  };
}

function verifyLane(policy, completions, semantic, expectedCandidateId, hashes) {
  if (completions.schema !== 'doppler.wgsl-writer-completions/v1'
    || completions.experimentId !== 'doppler-wgsl-writer-v1'
    || completions.evaluationRole !== 'visible_zero_shot_diagnostic'
    || completions.policy.path !== policy.__path
    || completions.policy.sha256 !== policy.__sha256
    || completions.population.path !== policy.population.path
    || completions.population.sha256 !== policy.population.sha256
    || !stableEqual(completions.referenceReceipt, policy.predecessor.referenceReceipt)
    || completions.candidate.id !== expectedCandidateId
    || completions.submission?.ordinalForCandidate !== 1
    || completions.submission?.retryPerformed !== false
    || completions.submission?.promptOrSamplerChangedAfterFreeze !== false
    || completions.selectionAuthority !== false
    || completions.confirmationAuthority !== false
    || completions.promotionAuthority !== false
    || completions.productizationAllowed !== false) {
    throw new Error(`${expectedCandidateId}: completion receipt binding failed.`);
  }
  if (semantic.schema !== 'doppler.wgsl-writer-semantic-dispatch-receipt/v1'
    || semantic.experimentId !== 'doppler-wgsl-writer-v1'
    || semantic.mode !== 'candidate'
    || semantic.candidate?.id !== expectedCandidateId
    || semantic.candidateCompletions?.sha256 !== hashes.completions
    || semantic.candidateCompletions?.receiptHash !== completions.receiptHash
    || semantic.policy?.path !== policy.predecessor.basePolicy.path
    || semantic.policy?.sha256 !== policy.predecessor.basePolicy.sha256
    || semantic.taskManifest?.path !== policy.population.path
    || semantic.taskManifest?.sha256 !== policy.population.sha256
    || semantic.selectionAuthority !== false
    || semantic.confirmationAuthority !== false
    || semantic.promotionAuthority !== false
    || semantic.completeShaderWritingEstablished !== false
    || semantic.productizationAllowed !== false) {
    throw new Error(`${expectedCandidateId}: semantic receipt binding failed.`);
  }
}

export async function finalizeWgslWriterV1Diagnostic(args) {
  const [policyValue, baseCompletions, baseSemantic, adapterCompletions, adapterSemantic] =
    await Promise.all([
      readJson(args.policyPath),
      readJson(args.baseCompletionsPath),
      readJson(args.baseSemanticPath),
      readJson(args.adapterCompletionsPath),
      readJson(args.adapterSemanticPath),
    ]);
  const policySha256 = await sha256File(args.policyPath);
  const policy = { ...policyValue, __path: args.policyPath, __sha256: policySha256 };
  const [basePolicy, referenceReceipt] = await Promise.all([
    readJson(policy.predecessor.basePolicy.path),
    readJson(policy.predecessor.referenceReceipt.path),
  ]);
  requireInternalReceiptHash(referenceReceipt, 'writer reference receipt');
  if (basePolicy.policyId !== 'doppler-wgsl-writer-v1'
    || referenceReceipt.decision !== policy.predecessor.referenceReceipt.requiredDecision
    || referenceReceipt.mode !== 'reference'
    || referenceReceipt.mechanicsQualificationAuthority !== true
    || referenceReceipt.selectionAuthority !== false
    || referenceReceipt.promotionAuthority !== false) {
    throw new Error('Writer diagnostic predecessor binding failed.');
  }
  for (const [receipt, label] of [
    [baseCompletions, 'base completion receipt'],
    [baseSemantic, 'base semantic receipt'],
    [adapterCompletions, 'adapter completion receipt'],
    [adapterSemantic, 'adapter semantic receipt'],
  ]) {
    requireInternalReceiptHash(receipt, label);
  }
  await Promise.all([
    requireFileHash(
      policy.predecessor.basePolicy.path,
      policy.predecessor.basePolicy.sha256,
      'writer base policy'
    ),
    requireFileHash(
      policy.predecessor.referenceReceipt.path,
      policy.predecessor.referenceReceipt.sha256,
      'writer reference receipt'
    ),
    requireFileHash(policy.population.path, policy.population.sha256, 'writer population'),
    requireFileHash(policy.candidateRunner.path, policy.candidateRunner.sha256, 'candidate runner'),
    requireFileHash(policy.semanticHarness.path, policy.semanticHarness.sha256, 'semantic harness'),
  ]);
  const hashes = {
    base: {
      completions: await sha256File(args.baseCompletionsPath),
      semantic: await sha256File(args.baseSemanticPath),
    },
    adapter: {
      completions: await sha256File(args.adapterCompletionsPath),
      semantic: await sha256File(args.adapterSemanticPath),
    },
  };
  verifyLane(policy, baseCompletions, baseSemantic, policy.candidateIds[0], hashes.base);
  verifyLane(policy, adapterCompletions, adapterSemantic, policy.candidateIds[1], hashes.adapter);
  if (!stableEqual(baseCompletions.candidate, basePolicy.candidateInitializations[0])
    || !stableEqual(adapterCompletions.candidate, basePolicy.candidateInitializations[1])
    || !stableEqual(baseCompletions.generation, basePolicy.generation)
    || !stableEqual(adapterCompletions.generation, basePolicy.generation)
    || !stableEqual(baseCompletions.promptContract, basePolicy.promptContract)
    || !stableEqual(adapterCompletions.promptContract, basePolicy.promptContract)
    || !stableEqual(baseCompletions.generation, adapterCompletions.generation)
    || !stableEqual(baseCompletions.promptContract, adapterCompletions.promptContract)
    || baseCompletions.tasks.length !== adapterCompletions.tasks.length
    || baseCompletions.tasks.some((task, index) => (
      task.taskId !== adapterCompletions.tasks[index]?.taskId
      || task.promptSha256 !== adapterCompletions.tasks[index]?.promptSha256
      || task.prompt !== adapterCompletions.tasks[index]?.prompt
    ))) {
    throw new Error('Matched zero-shot prompt or generation binding failed.');
  }
  const base = summarizeLane(
    baseCompletions,
    baseSemantic,
    { completions: args.baseCompletionsPath, semantic: args.baseSemanticPath },
    hashes.base
  );
  const adapter = summarizeLane(
    adapterCompletions,
    adapterSemantic,
    { completions: args.adapterCompletionsPath, semantic: args.adapterSemanticPath },
    hashes.adapter
  );
  const transferObserved = adapter.metrics.semanticTaskPasses
    > base.metrics.semanticTaskPasses;
  const anyCompleteWriterBehavior = base.completeVisibleMechanicsPass
    || adapter.completeVisibleMechanicsPass;
  const core = {
    schema: 'doppler.wgsl-writer-v1-zero-shot-diagnostic-result/v1',
    experimentId: 'doppler-wgsl-writer-v1',
    policy: { path: args.policyPath, sha256: policySha256 },
    predecessor: policy.predecessor,
    population: policy.population,
    matchedExecution: {
      identicalPrompts: true,
      identicalGeneration: true,
      submissionsPerCandidate: 1,
      retriesPerformed: false,
    },
    lanes: { base, repairAdapter: adapter },
    comparison: {
      semanticTaskPassDelta: adapter.metrics.semanticTaskPasses
        - base.metrics.semanticTaskPasses,
      compilationPassDelta: adapter.metrics.compilationPasses
        - base.metrics.compilationPasses,
      responseContractPassDelta: adapter.metrics.responseContractPasses
        - base.metrics.responseContractPasses,
      transferObserved,
      anyCompleteWriterBehavior,
      finding: anyCompleteWriterBehavior
        ? 'complete_shader_behavior_observed_on_visible_mechanics'
        : 'no_complete_shader_behavior_observed_on_visible_mechanics',
    },
    decision: 'zero_shot_diagnostic_complete',
    candidateSelected: false,
    writerCapabilityEstablished: false,
    confirmationAuthority: false,
    promotionAuthority: false,
    productizationAllowed: false,
    nextBoundary: 'Do not tune against the visible mechanics tasks. Build a separate writer-training corpus and freeze disjoint calibration, checkpoint-selection, seed-confirmation, and one-use promotion populations before making a writer capability claim.',
    claimBoundary: 'Both frozen initializations were evaluated once on visible mechanics-only tasks. This paired negative diagnostic can reject current zero-shot writer readiness; it cannot estimate general writer quality, select a candidate, or promote a product.',
  };
  return { ...core, receiptHash: hashWgslSemanticEvidenceValue(core) };
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const receipt = await finalizeWgslWriterV1Diagnostic(args);
  const outputPath = path.resolve(args.outputPath);
  await fs.mkdir(path.dirname(outputPath), { recursive: true });
  await fs.writeFile(outputPath, `${JSON.stringify(receipt, null, 2)}\n`, 'utf8');
  console.error(`[wgsl-writer-diagnostic] wrote ${args.outputPath}`);
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main().catch((error) => {
    console.error(error instanceof Error ? error.stack : String(error));
    process.exitCode = 1;
  });
}

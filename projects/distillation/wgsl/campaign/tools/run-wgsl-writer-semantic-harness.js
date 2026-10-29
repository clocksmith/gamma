#!/usr/bin/env node

import { createHash } from 'node:crypto';
import fs from 'node:fs/promises';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

import {
  evaluateWgslSemanticTaskEvidence,
  hashWgslSemanticEvidenceValue,
} from '../src/tooling/wgsl-repair-semantic-gate.js';
import { createWgslBrowserVerifier } from './lib/wgsl-browser-verifier.js';
import {
  runWgslWriterTaskManifest,
  summarizeWgslSemanticTaskEvidence,
} from './lib/wgsl-writer-semantic-harness.js';

const DEFAULT_POLICY = 'tools/policies/wgsl-writer-v1-policy.json';

function parseArgs(argv) {
  const args = {
    policyPath: DEFAULT_POLICY,
    mode: 'reference',
    completionsPath: '',
    outputPath: '',
  };
  for (let index = 0; index < argv.length; index += 1) {
    const token = argv[index];
    if (token === '--policy') args.policyPath = argv[++index] || '';
    else if (token === '--mode') args.mode = argv[++index] || '';
    else if (token === '--completions') args.completionsPath = argv[++index] || '';
    else if (token === '--out') args.outputPath = argv[++index] || '';
    else throw new Error(`Unknown argument: ${token}`);
  }
  if (!['reference', 'candidate'].includes(args.mode)) {
    throw new Error('--mode must be reference or candidate.');
  }
  if (args.mode === 'candidate' && !args.completionsPath) {
    throw new Error('--completions is required in candidate mode.');
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

async function loadReferenceShaders(manifest) {
  const references = {};
  for (const task of manifest.tasks || []) {
    await requireFileHash(
      task.referenceShaderPath,
      task.referenceShaderSha256,
      `${task.taskId} reference shader`
    );
    references[task.taskId] = (await fs.readFile(
      path.resolve(task.referenceShaderPath),
      'utf8'
    )).trim();
  }
  return references;
}

export async function runWgslWriterSemanticHarness(args) {
  const policy = await readJson(args.policyPath);
  if (policy?.policyId !== 'doppler-wgsl-writer-v1') {
    throw new Error('WGSL writer semantic harness: unsupported policy.');
  }
  await Promise.all([
    requireFileHash(
      policy.mechanics.taskManifest.path,
      policy.mechanics.taskManifest.sha256,
      'writer mechanics manifest'
    ),
    requireFileHash(
      policy.implementation.semanticHarness.path,
      policy.implementation.semanticHarness.sha256,
      'writer semantic harness'
    ),
    requireFileHash(
      policy.implementation.semanticLibrary.path,
      policy.implementation.semanticLibrary.sha256,
      'writer semantic library'
    ),
    requireFileHash(
      policy.implementation.repairSemanticLibrary.path,
      policy.implementation.repairSemanticLibrary.sha256,
      'delegated repair semantic library'
    ),
    requireFileHash(
      policy.implementation.browserVerifier.path,
      policy.implementation.browserVerifier.sha256,
      'writer browser verifier'
    ),
    requireFileHash(
      policy.implementation.historicalRegressions.path,
      policy.implementation.historicalRegressions.sha256,
      'writer historical regressions'
    ),
  ]);
  const manifest = await readJson(policy.mechanics.taskManifest.path);
  if (manifest?.schema !== 'doppler.wgsl-writer-task-manifest/v1'
    || manifest?.experimentId !== 'doppler-wgsl-writer-v1'
    || manifest?.role !== 'mechanics_qualification_only'
    || manifest?.populationAuthority !== 'none') {
    throw new Error('WGSL writer semantic harness: mechanics manifest is invalid.');
  }
  const referenceShaders = await loadReferenceShaders(manifest);
  const completionDocument = args.mode === 'candidate'
    ? await readJson(args.completionsPath)
    : null;
  if (completionDocument) {
    requireInternalReceiptHash(completionDocument, 'writer completion receipt');
    if (completionDocument.schema !== 'doppler.wgsl-writer-completions/v1'
      || completionDocument.experimentId !== 'doppler-wgsl-writer-v1'
      || completionDocument.population?.path !== policy.mechanics.taskManifest.path
      || completionDocument.population?.sha256 !== policy.mechanics.taskManifest.sha256
      || completionDocument.selectionAuthority !== false
      || completionDocument.promotionAuthority !== false) {
      throw new Error('WGSL writer semantic harness: candidate completions are not bound.');
    }
  }
  const verifier = await createWgslBrowserVerifier({
    requiredFeatures: [],
    progressEvery: 3,
  });
  try {
    const tasks = await runWgslWriterTaskManifest({
      manifest,
      referenceShaders,
      mode: args.mode,
      completions: completionDocument?.completions,
      responseContract: policy.taskContract.responseEnvelope,
      verifier,
    });
    const evaluatedTasks = tasks.map((task) => (
      evaluateWgslSemanticTaskEvidence(policy, task)
    ));
    const semanticTaskPasses = evaluatedTasks.filter((task) => task.pass).length;
    const allTasksPass = semanticTaskPasses === evaluatedTasks.length;
    const core = {
      schema: 'doppler.wgsl-writer-semantic-dispatch-receipt/v1',
      experimentId: 'doppler-wgsl-writer-v1',
      evaluationRole: manifest.role,
      mode: args.mode,
      candidate: args.mode === 'reference'
        ? { kind: 'reference_control', selectionAuthority: false }
        : completionDocument.candidate,
      candidateCompletions: args.mode === 'candidate'
        ? {
          path: args.completionsPath,
          sha256: await sha256File(args.completionsPath),
          receiptHash: completionDocument.receiptHash,
        }
        : null,
      policy: {
        path: args.policyPath,
        sha256: await sha256File(args.policyPath),
      },
      taskManifest: policy.mechanics.taskManifest,
      runtime: {
        backend: 'chromium_webgpu',
        deviceInfo: verifier.deviceInfo,
        browserArgs: verifier.browserArgs,
      },
      tasks,
      evaluatedTasks,
      summary: {
        ...summarizeWgslSemanticTaskEvidence(tasks),
        semanticTaskPasses,
      },
      decision: args.mode === 'reference'
        ? (allTasksPass ? 'reference_mechanics_passed' : 'reference_mechanics_failed')
        : (allTasksPass ? 'candidate_tasks_passed' : 'candidate_tasks_failed'),
      mechanicsQualificationAuthority: args.mode === 'reference',
      selectionAuthority: false,
      confirmationAuthority: false,
      promotionAuthority: false,
      completeShaderWritingEstablished: false,
      productizationAllowed: false,
      claimBoundary: args.mode === 'reference'
        ? 'A passing result qualifies the visible full-shader response, compilation, dispatch, CPU-oracle, bounds, shape, workgroup, metamorphic, and receipt mechanics only. It is not model capability evidence.'
        : 'A candidate result on the visible mechanics tasks is diagnostic only. It cannot select, confirm, promote, or productize a WGSL writer.',
    };
    return { ...core, receiptHash: hashWgslSemanticEvidenceValue(core) };
  } finally {
    await verifier.close();
  }
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const receipt = await runWgslWriterSemanticHarness(args);
  const json = `${JSON.stringify(receipt, null, 2)}\n`;
  if (args.outputPath) {
    const outputPath = path.resolve(args.outputPath);
    await fs.mkdir(path.dirname(outputPath), { recursive: true });
    await fs.writeFile(outputPath, json, 'utf8');
    console.error(`[wgsl-writer-semantic] wrote ${args.outputPath}`);
  } else {
    process.stdout.write(json);
  }
  if (!receipt.decision.endsWith('_passed')) process.exitCode = 1;
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main().catch((error) => {
    console.error(error instanceof Error ? error.stack : String(error));
    process.exitCode = 1;
  });
}

#!/usr/bin/env node

import { createHash } from 'node:crypto';
import fs from 'node:fs/promises';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

import { evaluateWgslSemanticTaskEvidence } from '../src/tooling/wgsl-repair-semantic-gate.js';
import { createWgslBrowserVerifier } from './lib/wgsl-browser-verifier.js';
import {
  runWgslWriterTaskManifest,
  summarizeWgslSemanticTaskEvidence,
} from './lib/wgsl-writer-semantic-harness.js';

const DEFAULT_POLICY = 'tools/policies/wgsl-writer-v2-corpus-policy.json';
const DEFAULT_OUTPUT =
  'reports/training/wgsl-writer/doppler-wgsl-writer-v2/corpus-v1/reference-qualification.json';

function parseArgs(argv) {
  const args = { policyPath: DEFAULT_POLICY, outputPath: DEFAULT_OUTPUT };
  for (let index = 0; index < argv.length; index += 1) {
    const token = argv[index];
    if (token === '--policy') args.policyPath = argv[++index] || '';
    else if (token === '--out') args.outputPath = argv[++index] || '';
    else throw new Error(`Unknown argument: ${token}`);
  }
  if (!args.policyPath || !args.outputPath) {
    throw new Error('--policy and --out require values.');
  }
  return args;
}

async function readJson(filePath) {
  return JSON.parse(await fs.readFile(path.resolve(filePath), 'utf8'));
}

async function sha256File(filePath) {
  return createHash('sha256').update(await fs.readFile(path.resolve(filePath))).digest('hex');
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

function verifyManifestHash(manifest) {
  const core = { ...manifest };
  delete core.manifestSha256;
  const actual = sha256Value(core);
  if (actual !== manifest.manifestSha256) {
    throw new Error(
      `WGSL writer corpus internal manifest hash mismatch: expected ${manifest.manifestSha256}, got ${actual}.`
    );
  }
}

async function readJsonl(filePath) {
  const raw = await fs.readFile(path.resolve(filePath), 'utf8');
  return raw.trim().split('\n').filter(Boolean).map((line, index) => {
    try {
      return JSON.parse(line);
    } catch (error) {
      throw new Error(`${filePath}:${index + 1}: ${error.message}`);
    }
  });
}

async function verifyBoundFiles(manifest) {
  for (const [filePath, binding] of Object.entries(manifest.fileBindings || {})) {
    await requireFileHash(filePath, binding.sha256, `writer corpus file ${filePath}`);
  }
}

async function loadRows(manifest) {
  const rows = [];
  for (const [role, population] of Object.entries(manifest.roles || {})) {
    await requireFileHash(
      population.datasetPath,
      population.datasetSha256,
      `${role} dataset`
    );
    const populationRows = await readJsonl(population.datasetPath);
    if (populationRows.length !== population.rows) {
      throw new Error(
        `${role} dataset row mismatch: expected ${population.rows}, got ${populationRows.length}.`
      );
    }
    if (populationRows.some((row) => row.populationRole !== role)) {
      throw new Error(`${role} dataset contains a role mismatch.`);
    }
    rows.push(...populationRows);
  }
  return rows;
}

async function loadReferenceShaders(taskManifest) {
  const references = {};
  for (const task of taskManifest.tasks || []) {
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

export async function qualifyWgslWriterCorpus(args) {
  const policy = await readJson(args.policyPath);
  if (policy?.policyId !== 'doppler-wgsl-writer-v2-corpus'
    || policy?.status !== 'frozen_before_materialization_and_training') {
    throw new Error('WGSL writer corpus qualification requires the frozen v2 corpus policy.');
  }
  const mechanicsPolicy = await readJson(policy.predecessor.mechanicsPolicy.path);
  const corpusManifestPath = path.join(policy.corpus.outputRoot, 'corpus-manifest.json');
  const corpusManifest = await readJson(corpusManifestPath);
  verifyManifestHash(corpusManifest);
  await Promise.all([
    requireFileHash(
      policy.predecessor.mechanicsPolicy.path,
      policy.predecessor.mechanicsPolicy.sha256,
      'writer mechanics policy'
    ),
    requireFileHash(
      policy.predecessor.referenceReceipt.path,
      policy.predecessor.referenceReceipt.sha256,
      'writer reference receipt'
    ),
    requireFileHash(
      policy.predecessor.zeroShotResult.path,
      policy.predecessor.zeroShotResult.sha256,
      'writer zero-shot result'
    ),
    requireFileHash(
      policy.corpus.blueprintCatalog.path,
      policy.corpus.blueprintCatalog.sha256,
      'writer blueprint catalog'
    ),
    verifyBoundFiles(corpusManifest),
  ]);
  if (corpusManifest.isolation?.semanticFamilyOverlaps?.length !== 0
    || corpusManifest.isolation?.duplicateRowIds !== 0
    || corpusManifest.isolation?.duplicatePrompts !== 0
    || corpusManifest.isolation?.visibleMechanicsPopulationUsedForTraining !== false) {
    throw new Error('WGSL writer corpus isolation gate failed.');
  }
  const rows = await loadRows(corpusManifest);
  const taskManifest = await readJson(
    corpusManifest.referenceQualification.taskManifestPath
  );
  const referenceShaders = await loadReferenceShaders(taskManifest);
  const verifier = await createWgslBrowserVerifier({
    requiredFeatures: [],
    progressEvery: 100,
  });
  try {
    const compilationResults = await verifier.compile(rows.map((row) => ({
      id: row.rowId,
      code: row.completion,
    })));
    const compilationFailures = compilationResults.filter((result) => result.passed !== true);
    const taskEvidence = await runWgslWriterTaskManifest({
      manifest: taskManifest,
      referenceShaders,
      mode: 'reference',
      responseContract: mechanicsPolicy.taskContract.responseEnvelope,
      verifier,
    });
    const evaluatedTasks = taskEvidence.map((task) => (
      evaluateWgslSemanticTaskEvidence(mechanicsPolicy, task)
    ));
    const semanticTaskPasses = evaluatedTasks.filter((task) => task.pass).length;
    const passed = compilationFailures.length === 0
      && semanticTaskPasses === evaluatedTasks.length;
    const core = {
      schema: 'doppler.wgsl-writer-corpus-qualification/v1',
      experimentId: policy.experimentId,
      policy: {
        path: args.policyPath,
        sha256: await sha256File(args.policyPath),
      },
      corpusManifest: {
        path: corpusManifestPath,
        sha256: await sha256File(corpusManifestPath),
        internalManifestSha256: corpusManifest.manifestSha256,
        corpusSha256: corpusManifest.corpusSha256,
      },
      referenceTaskManifest: {
        path: corpusManifest.referenceQualification.taskManifestPath,
        sha256: await sha256File(
          corpusManifest.referenceQualification.taskManifestPath
        ),
      },
      runtime: {
        backend: 'chromium_webgpu',
        deviceInfo: verifier.deviceInfo,
        browserArgs: verifier.browserArgs,
      },
      compilation: {
        shaderCount: rows.length,
        passes: compilationResults.length - compilationFailures.length,
        failures: compilationFailures.map((result) => ({
          id: result.id,
          error: result.error || null,
          compilation: result.compilation || null,
        })),
        passedIdsSha256: sha256Value(
          compilationResults.filter((result) => result.passed).map((result) => result.id)
        ),
      },
      semantic: {
        ...summarizeWgslSemanticTaskEvidence(taskEvidence),
        semanticTaskPasses,
        evaluatedTasks,
      },
      decision: passed ? 'reference_corpus_qualified' : 'reference_corpus_rejected',
      trainingAdmission: passed,
      selectionAuthority: false,
      confirmationAuthority: false,
      promotionAuthority: false,
      completeShaderWritingEstablished: false,
      productizationAllowed: false,
      claimBoundary: 'A pass admits the frozen v2 corpus to training by proving all materialized target shaders compile and all heldout tasks plus one representative per training family pass reference semantic dispatch. It contains no model capability evidence.',
    };
    return { ...core, receiptHash: sha256Value(core) };
  } finally {
    await verifier.close();
  }
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const receipt = await qualifyWgslWriterCorpus(args);
  const outputPath = path.resolve(args.outputPath);
  await fs.mkdir(path.dirname(outputPath), { recursive: true });
  await fs.writeFile(outputPath, `${JSON.stringify(receipt, null, 2)}\n`, 'utf8');
  console.error(`[wgsl-writer-corpus] wrote ${args.outputPath}`);
  process.stdout.write(`${JSON.stringify({
    decision: receipt.decision,
    compilation: receipt.compilation,
    semantic: {
      taskCount: receipt.semantic.taskCount,
      semanticTaskPasses: receipt.semantic.semanticTaskPasses,
      dispatchVariantCount: receipt.semantic.dispatchVariantCount,
      dispatchVariantPasses: receipt.semantic.dispatchVariantPasses,
    },
    receiptHash: receipt.receiptHash,
  }, null, 2)}\n`);
  if (receipt.trainingAdmission !== true) process.exitCode = 1;
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main().catch((error) => {
    console.error(error instanceof Error ? error.stack : String(error));
    process.exitCode = 1;
  });
}

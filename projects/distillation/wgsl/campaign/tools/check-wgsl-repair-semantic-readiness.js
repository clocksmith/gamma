#!/usr/bin/env node

import { createHash } from 'node:crypto';
import fs from 'node:fs/promises';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

import {
  evaluateWgslSemanticReadiness,
  evaluateWgslSemanticReadinessV2,
} from '../src/tooling/wgsl-repair-semantic-gate.js';

const DEFAULT_POLICY = 'tools/policies/wgsl-repair-v13-semantic-policy.json';
const DEFAULT_STATE = 'tools/data/wgsl-repair-v13-semantic-evidence-state.json';

function parseArgs(argv) {
  const args = {
    policyPath: DEFAULT_POLICY,
    statePath: DEFAULT_STATE,
    evidencePath: '',
    outputPath: '',
    allowBlocked: false,
    legacyV1: false,
  };
  for (let index = 0; index < argv.length; index += 1) {
    const token = argv[index];
    if (token === '--policy') args.policyPath = argv[++index] || '';
    else if (token === '--state') args.statePath = argv[++index] || '';
    else if (token === '--evidence') args.evidencePath = argv[++index] || '';
    else if (token === '--out') args.outputPath = argv[++index] || '';
    else if (token === '--allow-blocked') args.allowBlocked = true;
    else if (token === '--legacy-v1') args.legacyV1 = true;
    else throw new Error(`Unknown argument: ${token}`);
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

function samePath(left, right) {
  return path.resolve(left) === path.resolve(right);
}

async function verifyOptionalBinding(filePath, expectedSha256) {
  if (!filePath || !expectedSha256) return false;
  try {
    return await sha256File(filePath) === expectedSha256;
  } catch {
    return false;
  }
}

export async function runWgslSemanticReadinessGate(args) {
  const policy = await readJson(args.policyPath);
  const predecessorChecks = await Promise.all([
    sha256File(policy.predecessor.resultPath),
    sha256File(policy.predecessor.preservationVerificationPath),
  ]);
  const predecessorVerified = predecessorChecks[0] === policy.predecessor.resultSha256
    && predecessorChecks[1] === policy.predecessor.preservationVerificationSha256;
  const preservationReceipt = await readJson(policy.predecessor.preservationVerificationPath);
  const taskEvidence = args.evidencePath
    ? (await readJson(args.evidencePath)).tasks
    : [];
  if (args.legacyV1 === true) {
    return evaluateWgslSemanticReadiness({
      policy,
      predecessorVerified,
      preservationReceipt,
      taskEvidence,
    });
  }

  const evidenceState = await readJson(args.statePath || DEFAULT_STATE);
  const policyVerified = samePath(args.policyPath, evidenceState.policy?.path)
    && await verifyOptionalBinding(evidenceState.policy?.path, evidenceState.policy?.sha256);
  const adapterPortabilityReceiptVerified = await verifyOptionalBinding(
    evidenceState.adapterPortability?.path,
    evidenceState.adapterPortability?.sha256
  );
  const adapterPortabilityReceipt = await readJson(evidenceState.adapterPortability.path);
  const populationVerification = Object.fromEntries(await Promise.all(
    Object.entries(evidenceState.populations).map(async ([role, population]) => [
      role,
      population?.status === 'frozen'
        && await verifyOptionalBinding(population.manifestPath, population.populationHash),
    ])
  ));
  const selectionReceiptVerified = evidenceState.candidate?.seedSelectionStatus === 'selected'
    && await verifyOptionalBinding(
      evidenceState.candidate.selectionReceiptPath,
      evidenceState.candidate.selectionReceiptSha256
    )
    && await verifyOptionalBinding(
      evidenceState.candidate.adapterPath,
      evidenceState.candidate.adapterSha256
    );
  const selectionReceipt = evidenceState.candidate?.seedSelectionStatus === 'selected'
    ? await readJson(evidenceState.candidate.selectionReceiptPath)
    : null;
  const seedConfirmationReceiptVerified = evidenceState.seedConfirmation != null
    && await verifyOptionalBinding(
      evidenceState.seedConfirmation.receiptPath,
      evidenceState.seedConfirmation.receiptSha256
    );
  const seedConfirmationReceipt = evidenceState.seedConfirmation != null
    ? await readJson(evidenceState.seedConfirmation.receiptPath)
    : null;
  const implementationVerification = {
    taskManifest: await verifyOptionalBinding(
      evidenceState.implementation.taskManifestPath,
      evidenceState.implementation.taskManifestSha256
    ),
    historicalRegressionManifest: await verifyOptionalBinding(
      evidenceState.implementation.historicalRegressionManifestPath,
      evidenceState.implementation.historicalRegressionManifestSha256
    ),
  };
  return evaluateWgslSemanticReadinessV2({
    policy,
    evidenceState,
    policyVerified,
    predecessorVerified,
    preservationReceipt,
    adapterPortabilityReceipt,
    adapterPortabilityReceiptVerified,
    populationVerification,
    selectionReceipt,
    selectionReceiptVerified,
    seedConfirmationReceipt,
    seedConfirmationReceiptVerified,
    implementationVerification,
    taskEvidence,
  });
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const receipt = await runWgslSemanticReadinessGate(args);
  const json = `${JSON.stringify(receipt, null, 2)}\n`;
  if (args.outputPath) {
    const outputPath = path.resolve(args.outputPath);
    await fs.mkdir(path.dirname(outputPath), { recursive: true });
    await fs.writeFile(outputPath, json, 'utf8');
    console.error(`[wgsl-semantic-readiness] wrote ${args.outputPath}`);
  } else {
    process.stdout.write(json);
  }
  if (receipt.decision === 'blocked' && !args.allowBlocked) process.exitCode = 1;
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main().catch((error) => {
    console.error(error instanceof Error ? error.message : String(error));
    process.exitCode = 1;
  });
}

#!/usr/bin/env node

import { createHash } from 'node:crypto';
import fs from 'node:fs/promises';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

import { hashWgslSemanticEvidenceValue } from '../src/tooling/wgsl-repair-semantic-gate.js';

const CAMPAIGN_PATH = 'tools/policies/wgsl-writer-v3-campaign-policy.json';
const OUTPUT_PATH = 'docs/status/wgsl-writer-v3-campaign-reconciliation-2026-07-19.json';
const EXPOSURE_LEDGER_SCHEMA_SHA256 = '5262a2ed29dd97d163c49f21ab69b54103dc524c68959dc0561defb128fdc038';
const DEVELOPMENT_POLICIES = Object.freeze([
  'tools/policies/wgsl-writer-v3-training-policy.json',
  'tools/policies/wgsl-writer-v3-diversity-training-policy.json',
  'tools/policies/wgsl-writer-v3-explicit-semantic-training-policy.json',
  'tools/policies/wgsl-writer-v3-explicit-budget-training-policy.json',
]);

async function sha256File(filePath) {
  return createHash('sha256').update(await fs.readFile(filePath)).digest('hex');
}

async function readJson(filePath) {
  return JSON.parse(await fs.readFile(filePath, 'utf8'));
}

async function binding(filePath) {
  return { path: filePath, sha256: await sha256File(filePath) };
}

async function observedPolicy(filePath) {
  const policy = await readJson(filePath);
  const referencedPaths = Object.values(policy.admission || {})
    .map((entry) => entry?.path)
    .filter(Boolean);
  const missingReferences = [];
  for (const referencedPath of referencedPaths) {
    try {
      await fs.access(referencedPath);
    } catch {
      missingReferences.push(referencedPath);
    }
  }
  return {
    ...(await binding(filePath)),
    policyId: policy.policyId,
    artifactRoot: policy.artifactRoot || null,
    role: 'development',
    missingReferences,
  };
}

export async function reconcileWgslWriterV3Campaign({
  campaignPath = CAMPAIGN_PATH,
  outputPath = OUTPUT_PATH,
  repositoryRevision = null,
} = {}) {
  const campaign = await readJson(campaignPath);
  const policies = await Promise.all(DEVELOPMENT_POLICIES.map(observedPolicy));
  let originalGate = null;
  if (campaign.reconciliation?.receipt?.path) {
    const priorReconciliation = await readJson(campaign.reconciliation.receipt.path);
    originalGate = priorReconciliation.originalGate;
  } else {
    originalGate = {
      ...(await binding(campaignPath)),
      repositoryRevision,
      status: campaign.status,
      trainingAllowed: campaign.training?.allowed === true,
      corpusMaterializationAuthority: campaign.authority?.corpusMaterialization === true,
      promotionAuthority: campaign.authority?.promotion === true,
    };
  }
  const core = {
    schema: 'doppler.wgsl-writer-v3-campaign-reconciliation/v1',
    experimentId: 'doppler-wgsl-writer-v3',
    recordedAt: '2026-07-19T00:00:00.000Z',
    exposureLedgerContract: {
      schema: 'clocksmith.exposure-ledger/v1',
      schemaSha256: EXPOSURE_LEDGER_SCHEMA_SHA256,
    },
    originalGate,
    laterPolicies: policies,
    findings: [
      'canonical_campaign_blocks_corpus_materialization_and_training',
      'later_development_policies_exist_without_a_campaign_transition_receipt',
      'later_policy_materialization_training_selection_and_confirmation_artifacts_are_not_present',
    ],
    resolution: {
      canonicalStatus: 'developmental_policies_reconciled_prospective_materialization_blocked',
      experimentState: 'frozen',
      laterPolicyRole: 'development',
      existingResultsRole: 'development',
      selectionAuthority: false,
      confirmationAuthority: false,
      promotionAuthority: false,
      historicalGatePreserved: true,
      prospectiveCampaignRequired: true,
    },
    nextRequiredTransition: {
      from: 'frozen',
      to: 'materialized',
      requirements: [
        'new_family_disjoint_populations',
        'immutable_artifact_and_evaluator_custody',
        'exposure_ledger_registration',
        'eligible_pool_counts_before_freeze',
        'duplicate_and_connected_component_split_receipts',
      ],
    },
    claimBoundary: 'Later V3 policies are preserved as developmental evidence. They do not override the original blocked campaign gate and grant no selection, confirmation, promotion, general WGSL writer, or product authority.',
  };
  const receipt = { ...core, receiptHash: hashWgslSemanticEvidenceValue(core) };
  await fs.mkdir(path.dirname(outputPath), { recursive: true });
  await fs.writeFile(outputPath, `${JSON.stringify(receipt, null, 2)}\n`, 'utf8');
  return { outputPath, receipt };
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  reconcileWgslWriterV3Campaign({ repositoryRevision: process.env.DOPPLER_RECONCILIATION_REVISION || null })
    .then(({ outputPath, receipt }) => process.stdout.write(`${JSON.stringify({ outputPath, receiptHash: receipt.receiptHash }, null, 2)}\n`))
    .catch((error) => {
      console.error(error instanceof Error ? error.stack : String(error));
      process.exitCode = 1;
    });
}

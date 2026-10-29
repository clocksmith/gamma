#!/usr/bin/env node

import { createHash } from 'node:crypto';
import fs from 'node:fs/promises';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

import { sha256Hex } from '../src/utils/sha256.js';
import { stableSortObject } from '../src/utils/stable-sort-object.js';

const DEFAULT_MANIFEST = 'docs/status/wgsl-repair-v12-adapter-preservation-2026-07-13.json';

function hashStableJson(value) {
  return sha256Hex(JSON.stringify(stableSortObject(value)));
}

function parseArgs(argv) {
  const args = { manifestPath: DEFAULT_MANIFEST, allowLocalOnly: false };
  for (let index = 0; index < argv.length; index += 1) {
    const token = argv[index];
    if (token === '--manifest') args.manifestPath = argv[++index] || '';
    else if (token === '--allow-local-only') args.allowLocalOnly = true;
    else throw new Error(`Unknown argument: ${token}`);
  }
  return args;
}

async function fileIdentity(repoRoot, identity) {
  const filePath = path.resolve(repoRoot, identity.path || identity.localPath);
  try {
    const bytes = await fs.readFile(filePath);
    const stat = await fs.stat(filePath);
    const observedSha256 = createHash('sha256').update(bytes).digest('hex');
    const expectedBytes = identity.bytes ?? stat.size;
    return {
      path: identity.path || identity.localPath,
      present: true,
      expectedSha256: identity.sha256,
      observedSha256,
      expectedBytes,
      observedBytes: stat.size,
      ok: observedSha256 === identity.sha256 && stat.size === expectedBytes,
    };
  } catch (error) {
    return {
      path: identity.path || identity.localPath,
      present: false,
      expectedSha256: identity.sha256,
      observedSha256: null,
      expectedBytes: identity.bytes ?? null,
      observedBytes: null,
      ok: false,
      error: error instanceof Error ? error.message : String(error),
    };
  }
}

export async function verifyWgslV12AdapterPreservation(options = {}) {
  const repoRoot = path.resolve(options.repoRoot || '.');
  const manifestPath = path.resolve(repoRoot, options.manifestPath || DEFAULT_MANIFEST);
  const manifest = JSON.parse(await fs.readFile(manifestPath, 'utf8'));
  const sourceReceipt = await fileIdentity(repoRoot, manifest.sourceReceipt);
  const artifacts = [];
  for (const artifact of manifest.artifacts || []) {
    const [adapter, exportReceipt] = await Promise.all([
      fileIdentity(repoRoot, {
        localPath: artifact.localPath,
        sha256: artifact.sha256,
        bytes: artifact.bytes,
      }),
      fileIdentity(repoRoot, artifact.exportReceipt),
    ]);
    artifacts.push({
      seed: artifact.seed,
      checkpointStep: artifact.checkpointStep,
      adapter,
      exportReceipt,
      immutableUrl: artifact.immutableUrl,
      externalVerification: artifact.externalVerification ?? null,
    });
  }
  const localVerified = sourceReceipt.ok
    && artifacts.length === 3
    && artifacts.every((artifact) => artifact.adapter.ok && artifact.exportReceipt.ok);
  const immutableUrlsPresent = artifacts.length === 3
    && artifacts.every((artifact) => typeof artifact.immutableUrl === 'string' && artifact.immutableUrl);
  const externalIdentitiesVerified = artifacts.length === 3
    && artifacts.every((artifact) => (
      artifact.externalVerification?.method === 'streamed_https_sha256'
      && typeof artifact.externalVerification.verifiedAt === 'string'
      && artifact.externalVerification.observedSha256 === artifact.adapter.expectedSha256
      && artifact.externalVerification.ok === true
    ));
  const externallyPreserved = immutableUrlsPresent
    && externalIdentitiesVerified
    && manifest.externalPreservation?.status === 'complete';
  const blockers = [];
  if (!localVerified) blockers.push('v12_adapter_local_identity_verification_failed');
  if (!immutableUrlsPresent) blockers.push('v12_adapter_immutable_urls_absent');
  if (!externalIdentitiesVerified) {
    blockers.push('v12_adapter_external_identity_verification_failed');
  }
  if (manifest.externalPreservation?.status !== 'complete') {
    blockers.push('v12_adapter_governed_external_preservation_incomplete');
  }
  const core = {
    schema: 'doppler.wgsl-v12-adapter-preservation-verification/v1',
    experimentId: manifest.experimentId,
    lane: manifest.lane,
    sourceReceipt,
    artifacts,
    localVerified,
    immutableUrlsPresent,
    externalIdentitiesVerified,
    externallyPreserved,
    decision: localVerified && externallyPreserved ? 'complete' : localVerified ? 'local_verified' : 'blocked',
    blockers: [...new Set(blockers)].sort(),
    claimBoundary: 'Local and external identity verification establish preservation only; they do not establish adapter selection, inference parity, semantic WGSL evaluation, or promotion.',
  };
  return { ...core, receiptHash: hashStableJson(core) };
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const receipt = await verifyWgslV12AdapterPreservation({ manifestPath: args.manifestPath });
  process.stdout.write(`${JSON.stringify(receipt, null, 2)}\n`);
  if (receipt.decision !== 'complete' && !(args.allowLocalOnly && receipt.localVerified)) {
    process.exitCode = 1;
  }
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main().catch((error) => {
    console.error(error instanceof Error ? error.message : String(error));
    process.exitCode = 1;
  });
}

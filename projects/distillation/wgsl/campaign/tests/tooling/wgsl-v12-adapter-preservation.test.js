import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { mkdtempSync, mkdirSync, rmSync, writeFileSync } from 'node:fs';
import os from 'node:os';
import path from 'node:path';

import { verifyWgslV12AdapterPreservation } from '../../tools/verify-wgsl-v12-adapter-preservation.js';

const root = mkdtempSync(path.join(os.tmpdir(), 'doppler-wgsl-v12-preservation-'));
try {
  mkdirSync(path.join(root, 'artifacts'), { recursive: true });
  writeFileSync(path.join(root, 'source.json'), '{}');
  const sourceSha = createHash('sha256').update('{}').digest('hex');
  const artifacts = [];
  for (const seed of [11, 29, 47]) {
    const adapterPath = `artifacts/seed${seed}.safetensors`;
    const receiptPath = `artifacts/seed${seed}.json`;
    const adapterBytes = Buffer.from(`adapter-${seed}`);
    const receiptBytes = Buffer.from(`{"seed":${seed}}`);
    writeFileSync(path.join(root, adapterPath), adapterBytes);
    writeFileSync(path.join(root, receiptPath), receiptBytes);
    artifacts.push({
      seed,
      checkpointStep: 1200,
      localPath: adapterPath,
      sha256: createHash('sha256').update(adapterBytes).digest('hex'),
      bytes: adapterBytes.length,
      exportReceipt: {
        path: receiptPath,
        sha256: createHash('sha256').update(receiptBytes).digest('hex'),
      },
      immutableUrl: null,
    });
  }
  const manifest = {
    experimentId: 'unit-v12',
    lane: 'external20',
    sourceReceipt: { path: 'source.json', sha256: sourceSha },
    artifacts,
    externalPreservation: { status: 'blocked_missing_governed_destination' },
  };
  writeFileSync(path.join(root, 'manifest.json'), JSON.stringify(manifest));

  const local = await verifyWgslV12AdapterPreservation({
    repoRoot: root,
    manifestPath: 'manifest.json',
  });
  assert.equal(local.decision, 'local_verified');
  assert.equal(local.localVerified, true);
  assert.equal(local.externallyPreserved, false);
  assert.ok(local.blockers.includes('v12_adapter_immutable_urls_absent'));
  assert.ok(local.blockers.includes('v12_adapter_external_identity_verification_failed'));

  manifest.artifacts = manifest.artifacts.map((artifact) => ({
    ...artifact,
    immutableUrl: `https://artifacts.example/${artifact.sha256}`,
    externalVerification: {
      method: 'streamed_https_sha256',
      verifiedAt: '2026-07-13',
      observedSha256: artifact.sha256,
      ok: true,
    },
  }));
  manifest.externalPreservation.status = 'complete';
  writeFileSync(path.join(root, 'manifest.json'), JSON.stringify(manifest));
  const complete = await verifyWgslV12AdapterPreservation({
    repoRoot: root,
    manifestPath: 'manifest.json',
  });
  assert.equal(complete.decision, 'complete');
  assert.equal(complete.blockers.length, 0);

  writeFileSync(path.join(root, artifacts[0].localPath), 'tampered');
  const tampered = await verifyWgslV12AdapterPreservation({
    repoRoot: root,
    manifestPath: 'manifest.json',
  });
  assert.equal(tampered.decision, 'blocked');
  assert.equal(tampered.localVerified, false);
} finally {
  rmSync(root, { recursive: true, force: true });
}

console.log('wgsl-v12-adapter-preservation.test: ok');

import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import test from 'node:test';

import { finalizeWgslWriterV3Confirmation } from '../../tools/finalize-wgsl-writer-v3-confirmation.js';

test('WGSL writer V3 confirmation halts before hashing nonfinite evidence', async () => {
  const root = await fs.mkdtemp(path.join(os.tmpdir(), 'doppler-v3-finite-'));
  const paths = Object.fromEntries(['policy', 'selection', 'evaluation', 'out'].map((name) => [name, path.join(root, `${name}.json`)]));
  try {
    await fs.writeFile(paths.policy, JSON.stringify({ experimentId: 'test', artifactRoot: root, evaluation: { confirmationSeeds: [29], minimumConfirmationPerSeedSemanticPassRate: 0.5, minimumConfirmationMeanSemanticPassRate: 0.75 }, claimBoundary: 'test only' }));
    await fs.writeFile(paths.selection, JSON.stringify({ decision: 'lane_selected', selected: { candidateId: 'lane' } }));
    await fs.writeFile(paths.evaluation, '{"candidates":[{"capabilityAuthority":true,"candidateId":"lane-seed29","adapterPath":"adapter","adapterTreeSha256":"abc","summary":{"semanticPassRate":1e400}}]}');
    await assert.rejects(
      finalizeWgslWriterV3Confirmation({ policyPath: paths.policy, selectionPath: paths.selection, evaluationPath: paths.evaluation, outputPath: paths.out }),
      /halted on a nonfinite/
    );
    await assert.rejects(fs.access(paths.out));
  } finally {
    await fs.rm(root, { recursive: true, force: true });
  }
});

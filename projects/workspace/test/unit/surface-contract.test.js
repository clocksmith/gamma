import assert from 'node:assert/strict';
import { mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { createCdpAdapter } from '../../src/adapters/cdp-adapter.js';
import { createPlaywrightAdapter } from '../../src/adapters/playwright-adapter.js';
import { loadServiceConfig } from '../../src/config.js';
import { WorkspaceService } from '../../src/service.js';
import { CHROMIUM_SURFACE_V1, requireChromiumSurfaceV1 } from '../../src/surface-contract.js';

const config = loadServiceConfig();
const stateDir = mkdtempSync(join(tmpdir(), 'gamma-surface-contract-'));
const options = { config, profileRoot: stateDir, artifactRoot: stateDir };
let opened = 0;
const legacy = {
  async openWorkspace() { opened++; },
  async snapshot() {}, async probeUrl() {}, async probeElement() {},
  async execute() {}, async close() { return []; },
};

try {
  for (const create of [createCdpAdapter, createPlaywrightAdapter]) {
    const adapter = create(options);
    assert.equal(adapter.surfaceVersion, CHROMIUM_SURFACE_V1);
    assert.strictEqual(requireChromiumSurfaceV1(adapter), adapter);
  }
  assert.strictEqual(requireChromiumSurfaceV1(legacy), legacy);
  assert.throws(() => requireChromiumSurfaceV1({ ...legacy, focusPage: true }), /focusPage/);
  await assert.rejects(WorkspaceService.open({
    stateDir, config, createAdapter: () => ({ ...legacy, surfaceVersion: 'unknown/v2' }),
  }), /Unsupported workspace surface contract version/);
  await assert.rejects(WorkspaceService.open({
    stateDir, config, createAdapter: () => ({ ...legacy, execute: undefined }),
  }), /missing required operation: execute/);
  assert.equal(opened, 0, 'invalid adapters must not open a surface');

  // The failed opens must release the journal lock for a valid retry.
  const service = await WorkspaceService.open({ stateDir, config, createAdapter: () => legacy });
  assert.deepEqual(await service.close(), { releases: [] });
  assert.equal(opened, 0, 'startup must preserve lazy surface opening');
} finally {
  rmSync(stateDir, { recursive: true, force: true });
}
console.log('ok: workspace surface ABI, required operations, fail-closed startup, journal lock and lazy ownership');

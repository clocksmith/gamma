// The product entry hands a host's commit authority to the service, so its verified-write gate runs.

import assert from 'node:assert/strict';
import { mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { openWorkspaceApp } from '../../src/client/main.js';

const planner = { async plan() { throw Error('no model calls in this test'); } };
const open = (commitAuthority) => {
  const stateDir = mkdtempSync(join(tmpdir(), 'app-commit-authority-'));
  return { stateDir, app: openWorkspaceApp({ stateDir, port: 0, headless: true, planner, commitAuthority }) };
};

// An incomplete authority reaches WorkspaceService.open, which refuses it.
const bad = open({});
try {
  await assert.rejects(bad.app, /A commit authority needs approvalFor, readLock and readRecord/);
} finally { rmSync(bad.stateDir, { recursive: true, force: true }); }

// A complete one opens.
const good = open({ approvalFor() { return null; }, readLock() { return null; }, readRecord() { return null; } });
try {
  await (await good.app).close();
} finally { rmSync(good.stateDir, { recursive: true, force: true }); }
console.log('app commit authority: forwarded');

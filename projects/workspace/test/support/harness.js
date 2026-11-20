// Fawn workspace tests — in-process service setup over the fake adapter.
import { mkdtempSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { loadServiceConfig } from '../../src/config.js';
import { WorkspaceService } from '../../src/service.js';
import { createOwnerSession } from '../../src/workflows/owner-session.js';
import { FakeAdapter, ORIGIN } from './fake-adapter.js';

const WORKSPACE_ID = 'ws-test';
const FORM_INTENT = 'form:contact';

function createClock(startMs = Date.parse('2026-10-14T12:00:00Z')) {
  let nowMs = startMs;
  return { now: () => nowMs, advance: (ms) => { nowMs += ms; } };
}

async function openFakeService({ stateDir, receiptsPath, clock, hooks, config = loadServiceConfig() }) {
  let adapter = null;
  const service = await WorkspaceService.open({
    stateDir,
    config,
    createAdapter: () => {
      adapter = new FakeAdapter({ receiptsPath });
      return adapter;
    },
    hooks,
    clock: clock.now,
  });
  return { service, adapter };
}

async function setupWorkspace({ hooks, config } = {}) {
  const root = mkdtempSync(join(tmpdir(), 'fawn-service-'));
  const stateDir = join(root, 'state');
  const receiptsPath = join(root, 'external-receipts.jsonl');
  const clock = createClock();
  const { service, adapter } = await openFakeService({ stateDir, receiptsPath, clock, hooks, config });
  const { adminCredential } = await service.createWorkspace({ workspaceId: WORKSPACE_ID });
  await service.grantAuthorization({
    workspaceId: WORKSPACE_ID,
    adminCredential,
    grantId: 'grant-agent-a',
    ownerId: 'agent-a',
    intents: [FORM_INTENT],
    actionKinds: ['navigate', 'click', 'fill', 'submit', 'download'],
    targetOrigins: [ORIGIN],
  });
  const owner = await service.assignOwner({ workspaceId: WORKSPACE_ID, adminCredential, ownerId: 'agent-a' });
  const session = createOwnerSession(service, { workspaceId: WORKSPACE_ID, ...owner });
  return { root, stateDir, receiptsPath, clock, service, adapter, adminCredential, owner, session };
}

export { FORM_INTENT, ORIGIN, WORKSPACE_ID, createClock, openFakeService, setupWorkspace };

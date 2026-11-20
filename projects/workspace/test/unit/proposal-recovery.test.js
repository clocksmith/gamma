// Correct malformed, positively never-dispatched proposals; preserve stop-on-unknown/authority loss.
import assert from 'node:assert/strict';
import { mkdtempSync, readFileSync, rmSync } from 'node:fs';
import { join } from 'node:path';
import { tmpdir } from 'node:os';
import { WorkspaceController } from '../../src/client/controller.js';
import { WorkspaceService } from '../../src/service.js';
import { loadServiceConfig } from '../../src/config.js';
import { PLANNER_TOOLS } from '../../src/client/planner.js';
import { CONDITION_FIELDS } from '../../src/conditions.js';
import { FakeAdapter, ORIGIN } from '../support/fake-adapter.js';

const config = { ...JSON.parse(readFileSync(new URL('../../config/fawn-workspace-client.json', import.meta.url))), maxTurns: 8 };
const correct = { kind: 'submit', target: { handle: 'hsend' }, effect: { external: true, effectKey: 'send-once' },
  completion: { completedWhen: [{ kind: 'element-text-includes', selector: '#receipt', value: 'Submission received' }] } };
for (const kind of Object.keys(CONDITION_FIELDS)) assert.ok(PLANNER_TOOLS.act.includes(kind), kind);
for (const [name, invalid, expectedCode] of [
  ['unsupported-condition', { ...correct, completion: { completedWhen: [{ kind: 'text-equals', selector: '#receipt', value: 'Submission received' }] } }, 'unsupported-condition'],
  ['missing-completion', { ...correct, completion: undefined }, 'invalid-command'],
]) {
  const root = mkdtempSync(join(tmpdir(), 'fawn-proposal-'));
  let service, controller, adapter, calls = 0;
  try {
    service = await WorkspaceService.open({ stateDir: join(root, 'service'), config: loadServiceConfig(),
      createAdapter: () => adapter = new FakeAdapter({ receiptsPath: join(root, 'receipts') }) });
    controller = new WorkspaceController({ service, stateDir: join(root, 'client'), config,
      planner: { identity: { model: 'controlled-repair' }, next: async context => {
        calls++;
        if (calls === 1 || calls === 3) {
          if (calls === 3) {
            const rejected = context.history.findLast(event => event.event === 'tool-failed');
            assert.equal(rejected.code, expectedCode);
            assert.equal(rejected.recoverable, true);
            assert.equal(rejected.details.neverDispatched.code, expectedCode);
            assert.equal(adapter.receipts().length, 0, 'Malformed proposals never reached the site');
          }
          return { tool: 'observe', input: {} };
        }
        if (calls === 2) return { tool: 'act', input: invalid };
        if (calls === 4) return { tool: 'act', input: correct };
        return { tool: 'finish', input: { summary: 'Sent once after correcting the rejected proposal.' } };
      } } });
    const { id } = await controller.create({ goal: name });
    await controller.navigate(id, { pageId: 'main', url: ORIGIN + '/form' });
    await controller.delegate(id, { pageIds: ['main'], origins: [ORIGIN], actionKinds: ['submit'], task: 'Send once' });
    await controller.active.get(id)?.done;
    assert.equal(controller.store.get(id).run.status, 'completed', controller.store.get(id).run.detail);
    assert.equal(calls, 5);
    assert.equal(adapter.receipts().length, 1);
    assert.equal(controller.store.get(id).activity.filter(event => event.event === 'tool-failed').length, 1);
  } finally { await controller?.close(); await service?.close(); rmSync(root, { recursive: true, force: true }); }
}

for (const scenario of ['unknown-after-effect', 'unauthorized']) {
  const root = mkdtempSync(join(tmpdir(), 'fawn-no-retry-'));
  let service, controller, adapter, calls = 0;
  try {
    service = await WorkspaceService.open({ stateDir: join(root, 'service'), config: loadServiceConfig(), createAdapter: () => {
      adapter = new FakeAdapter({ receiptsPath: join(root, 'receipts') });
      const execute = adapter.execute.bind(adapter);
      adapter.execute = async (id, request) => { const value = await execute(id, request);
        if (scenario === 'unknown-after-effect' && request.kind === 'submit') throw Error('Acknowledgement lost after commit');
        return value; };
      return adapter;
    } });
    controller = new WorkspaceController({ service, stateDir: join(root, 'client'), config,
      planner: { identity: {}, next: async () => {
        calls++;
        return calls === 1 ? { tool: 'observe', input: {} } : { tool: 'act', input: correct };
      } } });
    const { id } = await controller.create({ goal: scenario });
    await controller.navigate(id, { pageId: 'main', url: ORIGIN + '/form' });
    await controller.delegate(id, { pageIds: ['main'], origins: [ORIGIN],
      actionKinds: scenario === 'unauthorized' ? ['fill'] : ['submit'], task: 'A bounded action' });
    await controller.active.get(id)?.done;
    assert.equal(controller.store.get(id).run.status, 'needs-attention');
    assert.equal(calls, 2, 'No retry or additional model request after uncertainty or denied authority');
    assert.equal(adapter.receipts().length, scenario === 'unknown-after-effect' ? 1 : 0);
  } finally { await controller?.close(); await service?.close(); rmSync(root, { recursive: true, force: true }); }
}
console.log('ok: rejected proposal repair with exact service attestation; no unknown-effect or authority retry');

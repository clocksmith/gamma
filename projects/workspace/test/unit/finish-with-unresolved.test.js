// A model's finish proposal cannot establish an external action's outcome.
// Exercise the product controller, persistent service and an independent receipt.
import assert from 'node:assert/strict';
import { mkdtempSync, readFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { WorkspaceController } from '../../src/client/controller.js';
import { WorkspaceService } from '../../src/service.js';
import { loadServiceConfig } from '../../src/config.js';
import { FakeAdapter, ORIGIN } from '../support/fake-adapter.js';

const config = { ...JSON.parse(readFileSync(new URL('../../config/fawn-workspace-client.json', import.meta.url))), maxTurns: 8 };
const root = mkdtempSync(join(tmpdir(), 'fawn-finish-unresolved-'));
const receiptsPath = join(root, 'site-receipts');
const planner = steps => {
  let index = 0;
  return { identity: { model: 'controlled-completion' }, next: async () => steps[index++] ?? { tool: 'finish', input: { summary: 'Everything is done.' } } };
};
let service, controller;
try {
  let dropAcknowledgement = true;
  service = await WorkspaceService.open({ stateDir: join(root, 'service'), config: loadServiceConfig(), createAdapter: () => {
    const adapter = new FakeAdapter({ receiptsPath });
    const execute = adapter.execute.bind(adapter);
    adapter.execute = async (id, request) => {
      const result = await execute(id, request);
      if (dropAcknowledgement && request.kind === 'submit') {
        dropAcknowledgement = false;
        throw Error('Site committed the submission before the connection dropped');
      }
      return result;
    };
    return adapter;
  } });
  controller = new WorkspaceController({ service, stateDir: join(root, 'client'), config, planner: planner([
    { tool: 'observe', input: { pageId: 'main' } },
    { tool: 'act', input: { pageId: 'main', kind: 'submit', target: { handle: 'hsend' },
      effect: { external: true, effectKey: 'one-submission' },
      completion: { completedWhen: [{ kind: 'element-text-includes', selector: '#receipt', value: 'Submission received' }] } } },
    { tool: 'finish', input: { summary: 'The form has been sent.' } },
  ]) });
  const { id } = await controller.create({ goal: 'Send the form once and establish the result.' });
  await controller.navigate(id, { pageId: 'main', url: `${ORIGIN}/form` });
  const delegation = { pageIds: ['main'], origins: [ORIGIN], actionKinds: ['submit', 'navigate'], task: 'Send the form once.' };
  await controller.delegate(id, delegation);
  await controller.active.get(id)?.done;
  let workspace = await service.inspect(controller.admin(id));
  const uncertain = workspace.actions.find(action => action.isUncertain);
  assert.ok(uncertain, 'The lost acknowledgement is an unresolved action in the service');
  assert.equal(readFileSync(receiptsPath, 'utf8').trim().split('\n').length, 1);
  assert.equal(controller.store.get(id).run.status, 'needs-attention',
    'A first-run finish must not claim completion with an unknown external outcome');

  // Restart and hand off to a different model that immediately declares success.
  controller.store.close();
  await service.close();
  service = await WorkspaceService.open({ stateDir: join(root, 'service'), config: loadServiceConfig(),
    createAdapter: () => new FakeAdapter({ receiptsPath }) });
  controller = new WorkspaceController({ service, stateDir: join(root, 'client'), config, planner: planner([]) });
  await controller.restore();
  // The open page does not show the receipt, so the service's own check on resume establishes nothing.
  await controller.navigate(id, { pageId: 'main', url: `${ORIGIN}/form` });
  await controller.delegate(id, { ...delegation, resume: true, task: 'Continue the interrupted investigation.' });
  await controller.active.get(id)?.done;
  assert.equal(controller.store.get(id).run.status, 'needs-attention',
    'A returning model cannot dismiss an unresolved action by saying finish');
  assert.equal((await controller.handoff(id)).unresolvedActions.length, 1);

  // Once the live page establishes the result, finishing is valid without resending.
  await controller.takeOver(id);
  await controller.navigate(id, { pageId: 'main', url: `${ORIGIN}/form/done` });
  const checked = await controller.check(id, { actionId: uncertain.actionId });
  assert.equal(checked.reconciliation.result, 'effect-present');
  assert.equal((await controller.handoff(id)).unresolvedActions.length, 0);
  await controller.delegate(id, { ...delegation, resume: true, task: 'Summarize the established result.' });
  await controller.active.get(id)?.done;
  assert.equal(controller.store.get(id).run.status, 'completed');
  assert.equal(readFileSync(receiptsPath, 'utf8').trim().split('\n').length, 1, 'No duplicate external submission');
  console.log('ok: first and resumed completion require established external outcomes; reconciliation permits finish');
} finally {
  await controller?.close().catch(() => {});
  await service?.close().catch(() => {});
  rmSync(root, { recursive: true, force: true });
}

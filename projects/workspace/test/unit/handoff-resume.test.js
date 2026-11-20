// A resumed agent sees prior work and the human's note, cannot repeat an action whose
// outcome is unknown, and establishes that outcome from the live page instead.
import assert from 'node:assert/strict';
import { mkdtempSync, readFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { WorkspaceService } from '../../src/service.js';
import { loadServiceConfig } from '../../src/config.js';
import { WorkspaceController } from '../../src/client/controller.js';
import { FakeAdapter, ORIGIN } from '../support/fake-adapter.js';

const config = { ...JSON.parse(readFileSync(new URL('../../config/fawn-workspace-client.json', import.meta.url))), maxTurns: 6 };
const root = mkdtempSync(join(tmpdir(), 'fawn-handoff-'));
const stateDir = join(root, 'service'), clientDir = join(root, 'client'), receiptsPath = join(root, 'receipts');
const scripted = (steps) => { let i = 0; const seen = [];
  return { seen, identity: { model: 'scripted' }, next: async (context) => { seen.push(context); return steps[i++] ?? { tool: 'finish', input: { summary: 'done' } }; } }; };
let service, controller;
try {
  // Session A: the submit reaches the site, then its acknowledgement is lost.
  let lossy = true;
  service = await WorkspaceService.open({ stateDir, config: loadServiceConfig(), createAdapter: () => {
    const adapter = new FakeAdapter({ receiptsPath }), execute = adapter.execute.bind(adapter);
    adapter.execute = async (id, request) => { const result = await execute(id, request);
      if (lossy && request.kind === 'submit') { lossy = false; throw Error('connection reset after send'); } return result; };
    return adapter; } });
  const first = scripted([
    { tool: 'observe', input: { pageId: 'main' } },
    { tool: 'act', input: { pageId: 'main', kind: 'submit', target: { handle: 'hsend' }, effect: { external: true, effectKey: 'send-1' },
      completion: { completedWhen: [{ kind: 'element-text-includes', selector: '#receipt', value: 'Submission received' }] } } },
  ]);
  controller = new WorkspaceController({ service, stateDir: clientDir, config, planner: first });
  const { id } = await controller.create({ goal: 'Send the contact form once' });
  await controller.navigate(id, { pageId: 'main', url: `${ORIGIN}/form` });
  await controller.delegate(id, { pageIds: ['main'], origins: [ORIGIN], actionKinds: ['submit', 'fill'], task: 'Send the form' });
  await controller.active.get(id)?.done;
  assert.equal(controller.store.get(id).run.status, 'needs-attention');
  assert.equal(readFileSync(receiptsPath, 'utf8').trim().split('\n').length, 1, 'the site received one submission');
  // Crash without a graceful client close.
  controller.store.close(); await service.close();

  // Human: restart, read the handoff, leave a note.
  service = await WorkspaceService.open({ stateDir, config: loadServiceConfig(), createAdapter: () => new FakeAdapter({ receiptsPath }) });
  controller = new WorkspaceController({ service, stateDir: clientDir, config });
  await controller.restore();
  await controller.navigate(id, { pageId: 'main', url: `${ORIGIN}/form/done` });
  controller.humanNote(id, 'Check whether the form went through before sending again.');
  const brief = await controller.handoff(id);
  assert.equal(brief.unresolvedActions.length, 1);
  assert.equal(brief.unresolvedActions[0].kind, 'submit');
  assert.ok(brief.human.some(entry => entry.event === 'note' && entry.text.includes('before sending again')));
  assert.ok(brief.tried.some(entry => entry.tool === 'act' && entry.result?.isUncertain), 'the lost send is in what was tried');
  controller.planner = scripted([]);
  await assert.rejects(controller.delegate(id, { pageIds: ['main'], origins: [ORIGIN], actionKinds: ['submit'], task: 'Send it' }),
    /unresolved actions/, 'a fresh task cannot inherit an unknown outcome');
  controller.store.close(); await service.close();

  // Session B, another agent: a blind repeat is refused while the outcome is unknown.
  service = await WorkspaceService.open({ stateDir, config: loadServiceConfig(), createAdapter: () => new FakeAdapter({ receiptsPath }) });
  const blind = scripted([{ tool: 'act', input: { pageId: 'main', kind: 'submit', target: { handle: 'hsend' } } }]);
  controller = new WorkspaceController({ service, stateDir: clientDir, config, planner: blind });
  await controller.restore();
  // The page in front of this session does not show the receipt, so the automatic check proves nothing.
  await controller.navigate(id, { pageId: 'main', url: `${ORIGIN}/form` });
  await controller.delegate(id, { pageIds: ['main'], origins: [ORIGIN], actionKinds: ['submit', 'navigate'], task: 'Continue', resume: true });
  await controller.active.get(id)?.done;
  assert.match(controller.store.get(id).run.detail, /Establish every unresolved action/);
  const unproven = controller.store.get(id).activity.filter(event => event.automatic && event.event === 'tool-result');
  assert.equal(unproven.at(-1).output.reconciliation.result, 'inconclusive', 'an unmet completion condition settles nothing');
  assert.equal((await controller.handoff(id)).unresolvedActions.length, 1);
  assert.ok(blind.seen[0].handoff, 'the resumed agent receives the handoff');
  assert.ok(blind.seen[0].handoff.human.some(entry => entry.event === 'note'));

  // Session B again: establish the outcome from the page, then finish without resending.
  // Session B again, with the receipt page open: the service checks the action's own recorded
  // completion condition on resume, so the planner needs no observe or reconcile request.
  const careful = scripted([
    { tool: 'finish', input: { summary: 'The earlier send went through; nothing to resend.' } },
  ]);
  controller.planner = careful;
  await controller.navigate(id, { pageId: 'main', url: `${ORIGIN}/form/done` });
  await controller.delegate(id, { pageIds: ['main'], origins: [ORIGIN], actionKinds: ['submit', 'navigate'], task: 'Continue', resume: true });
  await controller.active.get(id)?.done;
  const project = controller.store.get(id);
  assert.equal(project.run.status, 'completed');
  const reconciled = project.activity.findLast(event => event.event === 'tool-result' && event.output?.reconciliation);
  assert.equal(reconciled.output.reconciliation.result, 'effect-present');
  assert.equal(reconciled.automatic, true);
  assert.equal(careful.seen.length, 1, 'one planner request: finish');
  assert.equal(careful.seen[0].handoff.unresolvedActions.length, 0, 'the resumed planner starts with the outcome established');
  assert.ok(careful.seen[0].history.some(entry => entry.event === 'tool-requested' && entry.tool === 'reconcile'), 'and sees how it was established');
  assert.equal((await controller.handoff(id)).unresolvedActions.length, 0);
  assert.equal(readFileSync(receiptsPath, 'utf8').trim().split('\n').length, 1, 'no duplicate submission');
  console.log('ok: handoff memory, blind-repeat refusal, inconclusive automatic check, automatic reconcile from the live page, zero duplicates');
} finally {
  await controller?.close().catch(() => {}); await service?.close().catch(() => {});
  rmSync(root, { recursive: true, force: true });
}

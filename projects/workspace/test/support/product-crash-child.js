// Test-owned process: stop exactly after a real browser effect, before its outcome
// can be journaled. The parent verifies the boundary and sends SIGKILL.
import { writeFileSync, readFileSync } from 'node:fs';
import { join } from 'node:path';
import { WorkspaceService } from '../../src/service.js';
import { WorkspaceController } from '../../src/client/controller.js';
import { createPlaywrightAdapter } from '../../src/adapters/playwright-adapter.js';
import { testBrowserSelection } from './browser-selection.js';
const [root, trackerUrl, comment] = process.argv.slice(2);
const selected = testBrowserSelection(root);
const client = { ...JSON.parse(readFileSync(new URL('../../config/fawn-workspace-client.json', import.meta.url))), maxTurns: 5 };
let service, controller, id, evidence, turn = 0;
try {
  service = await WorkspaceService.open({ stateDir: join(root, 'service'), config: selected.config, createAdapter: createPlaywrightAdapter,
    hooks: { afterEffect(request) {
      if (request.effect?.effectKey !== 'crash-post-once') return;
      writeFileSync(join(root, 'effect-boundary.json'), JSON.stringify({ id, evidenceId: evidence.id,
        actionId: request.actionId, grantId: request.grantId, pid: process.pid }));
      // Unlike a graceful close, a stopped process cannot append the outcome or
      // revoke its grant. Only this known test process stops itself.
      process.kill(process.pid, 'SIGSTOP');
    } } });
  const planner = { identity: { model: 'controlled-first-process' }, async next(context) {
    const step = turn++;
    if (step === 0 || step === 2) return { tool: 'observe', input: { pageId: 'main' } };
    const observed = context.history.findLast(event => event.event === 'tool-result' && event.output?.elements)?.output;
    if (step === 1) return { tool: 'act', input: { pageId: 'main', kind: 'fill',
      target: { handle: observed.elements.find(value => value.selector === '#body').handle }, params: { value: comment } } };
    if (step === 3) return { tool: 'act', input: { pageId: 'main', kind: 'submit',
      target: { handle: observed.elements.find(value => value.selector === '#post').handle },
      effect: { external: true, effectKey: 'crash-post-once' },
      completion: { completedWhen: [{ kind: 'element-text-includes', selector: '#comments', value: comment }] } } };
    throw Error('The process should have been killed before the post returned');
  } };
  controller = new WorkspaceController({ service, stateDir: join(root, 'client'), config: client, planner });
  ({ id } = await controller.create({ goal: 'Record the finding on the tracker exactly once, preserving evidence through a crash.' }));
  await controller.navigate(id, { pageId: 'main', url: trackerUrl });
  evidence = await controller.capture(id, { pageId: 'main' });
  process.send?.({ phase: 'created', id });
  await controller.delegate(id, { pageIds: ['main'], origins: [new URL(trackerUrl).origin], actionKinds: ['fill', 'submit', 'navigate'], task: 'Post the finding once.' });
  await controller.active.get(id)?.done;
  throw Error(`No process-death boundary reached: ${JSON.stringify(controller.store.get(id).run)}`);
} catch (error) {
  console.error(error.stack);
  await controller?.close().catch(() => {}); await service?.close().catch(() => {});
  process.exitCode = 1;
}

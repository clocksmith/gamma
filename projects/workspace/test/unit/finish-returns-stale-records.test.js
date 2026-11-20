// A finish that leaves saved conclusions marked as needing review is returned to the agent once,
// with the records named and the way to revise them. Through the real controller and planner path.
// The case comes from a retained trial: a resuming model read for fourteen requests, believed the
// record tool was unavailable and finished with its conclusions only in the summary.
import assert from 'node:assert/strict';
import { mkdtempSync, mkdirSync, readFileSync, writeFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { WorkspaceService } from '../../src/service.js';
import { loadServiceConfig } from '../../src/config.js';
import { WorkspaceController } from '../../src/client/controller.js';
import { unfinishedRecords } from '../../src/client/validity.js';
import { REPLY_PROTOCOL } from '../../src/client/cli-planner.js';
import { FakeAdapter, ORIGIN } from '../support/fake-adapter.js';

assert.match(REPLY_PROTOCOL, /cannot call the workspace tools yourself/);
assert.match(REPLY_PROTOCOL, /including record, is available/);

const config = { ...JSON.parse(readFileSync(new URL('../../config/fawn-workspace-client.json', import.meta.url))), maxTurns: 6 };
const root = mkdtempSync(join(tmpdir(), 'fawn-finish-stale-')), repository = join(root, 'repository');
mkdirSync(join(repository, 'src'), { recursive: true });
writeFileSync(join(repository, 'src/cache.js'), 'export const TTL_SECONDS = 300;\n');
let service, controller;
const seen = [];
const scripted = steps => { let index = 0; return { identity: { model: 'controlled' }, next: async context => { seen.push(context); const step = steps[index++];
  return typeof step === 'function' ? step(context) : step ?? { tool: 'finish', input: { summary: 'Done.' } }; } }; };
const delegation = { pageIds: ['main'], origins: [ORIGIN], actionKinds: ['navigate'], task: 'Finish the investigation on the sources as they are now.' };
const run = async (id, steps, turns = 6) => { controller.planner = scripted(steps); controller.config = { ...config, maxTurns: turns };
  await controller.delegate(id, { ...delegation, resume: true }); await controller.active.get(id)?.done; return controller.store.get(id); };
const events = (project, from) => project.activity.filter(event => event.seq > from);
try {
  service = await WorkspaceService.open({ stateDir: join(root, 'service'), config: loadServiceConfig(), createAdapter: () => new FakeAdapter({ receiptsPath: join(root, 'receipts') }) });
  controller = new WorkspaceController({ service, stateDir: join(root, 'client'), config, planner: null });
  await controller.restore();
  const { id } = await controller.create({ goal: 'Explain why prices go stale', repositoryRoot: repository });
  await controller.navigate(id, { pageId: 'main', url: `${ORIGIN}/form` });
  const cache = await controller.readRepository(id, { path: 'src/cache.js' });
  const finding = controller.record(id, { kind: 'finding', text: 'Prices are cached for five minutes (TTL_SECONDS = 300).', dependsOn: [cache.id] });
  assert.equal(unfinishedRecords(controller.store.get(id)), null, 'nothing is outstanding before the source changes');

  // The file changes; resuming re-reads it and marks the finding.
  writeFileSync(join(repository, 'src/cache.js'), 'export const TTL_SECONDS = 900;\n');
  let mark = controller.store.journal.records.at(-1).seq;
  // First agent: finishes straight away, is told what is outstanding, revises the record, finishes.
  let project = await run(id, [
    { tool: 'finish', input: { summary: 'INCOMPLETE: the record tool was not callable.' } },
    context => { const returned = context.history.findLast(event => event.event === 'tool-failed');
      assert.equal(returned.code, 'finish-incomplete'); assert.equal(returned.recoverable, true);
      assert.match(returned.error, new RegExp(`${finding.id} \\(finding, revision 1\\)`)); assert.match(returned.error, /record tool is available through your reply/);
      return { tool: 'record', input: { id: finding.id, expectedRevision: 1, kind: 'finding', text: 'Prices are cached for fifteen minutes (TTL_SECONDS = 900).', dependsOn: [cache.id] } }; },
    { tool: 'finish', input: { summary: 'The finding now matches the source.' } },
  ]);
  assert.equal(project.run.status, 'completed', project.run.detail);
  assert.equal(project.artifacts[finding.id].status, 'current'); assert.equal(project.artifacts[finding.id].revision, 2);
  assert.equal(events(project, mark).filter(event => event.event === 'finish').length, 1, 'the returned finish is not recorded as a finish');
  assert.equal(events(project, mark).filter(event => event.code === 'finish-incomplete').length, 1);

  // Second change. This agent insists: the second finish is accepted, and the run is not called complete.
  writeFileSync(join(repository, 'src/cache.js'), 'export const TTL_SECONDS = 60;\n');
  mark = controller.store.journal.records.at(-1).seq;
  project = await run(id, [{ tool: 'finish', input: { summary: 'Done.' } }, { tool: 'finish', input: { summary: 'Still done.' } }]);
  assert.equal(project.run.status, 'needs-attention');
  assert.match(project.run.detail, /1 saved record\(s\) still need rechecking/);
  assert.equal(events(project, mark).filter(event => event.code === 'finish-incomplete').length, 1, 'a finish is returned at most once per run');
  assert.equal(project.run.turns, 2);

  // With no request left to act on it, the finish is not returned; the status still says what is outstanding.
  mark = controller.store.journal.records.at(-1).seq;
  project = await run(id, [{ tool: 'finish', input: { summary: 'Out of requests.' } }], 1);
  assert.equal(events(project, mark).filter(event => event.code === 'finish-incomplete').length, 0);
  assert.equal(project.run.status, 'needs-attention');
  console.log('ok: a finish that leaves marked records unrevised is returned once with the records named; insisting or running out of requests ends as needs-attention');
} finally {
  controller?.store.close(); await service?.close().catch(() => {});
  rmSync(root, { recursive: true, force: true });
}

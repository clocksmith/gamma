// A saved conclusion that names code is answered with where that code also occurs in saved sources
// the agent was not shown. The case comes from two graded trial runs: the agent recorded that a
// close "waits with no deadline" from one file, and never opened the part of another saved file
// (past the first 6000 characters) where the deadline is set.
import assert from 'node:assert/strict';
import { mkdtempSync, mkdirSync, readFileSync, writeFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { WorkspaceService } from '../../src/service.js';
import { loadServiceConfig } from '../../src/config.js';
import { WorkspaceController } from '../../src/client/controller.js';
import { codeTerms, claimsAbsence, shownRanges, unreadMentions, SHOWN_AT_FIRST_CHARS } from '../../src/client/unread-mentions.js';
import { FakeAdapter, ORIGIN } from '../support/fake-adapter.js';

assert.deepEqual(codeTerms('Browser.close() awaits options.browserProcess.close() in browser.js; see close_or_kill and README.md'),
  ['browserProcess', 'close_or_kill'], 'camelCase and snake_case parts only; file names and plain words are not code terms');
assert.deepEqual(codeTerms('The stall lasts as long as Chrome takes to exit.'), []);
for (const text of ['Playwright waits with no deadline.', 'close awaits the event without any timeout', 'the wait is unbounded', 'There is no retry limit', 'It never applies a guard']) assert.equal(claimsAbsence(text), true, text);
for (const text of ['The close is bounded at 15 s.', 'Chrome took 586 s to exit.', 'There is no reason to doubt the figure.']) assert.equal(claimsAbsence(text), false, text);

const config = { ...JSON.parse(readFileSync(new URL('../../config/fawn-workspace-client.json', import.meta.url))), maxTurns: 6 };
const root = mkdtempSync(join(tmpdir(), 'fawn-unread-')), repository = join(root, 'repository');
mkdirSync(join(repository, 'lib'), { recursive: true });
const filler = '// unrelated launcher code\n'.repeat(260);
assert.ok(filler.length > SHOWN_AT_FIRST_CHARS);
const LAUNCHER = `let browserProcess = void 0;\n${filler}async function closeOrKill(timeout) { /* race graceful close against a timer, then kill */ }\n`
  + 'browserProcess = { close: () => closeOrKill(DEFAULT_TIMEOUT) };\n';
writeFileSync(join(repository, 'lib/launcher.js'), LAUNCHER);
writeFileSync(join(repository, 'lib/browser.js'), 'export class Browser {\n  async close() { await this.options.browserProcess.close(); await this.disconnected; }\n}\n');
let service, controller;
try {
  service = await WorkspaceService.open({ stateDir: join(root, 'service'), config: loadServiceConfig(), createAdapter: () => new FakeAdapter({ receiptsPath: join(root, 'receipts') }) });
  let index = 0, seenResult = null, returned = null;
  const steps = [
    { tool: 'repository_read', input: { path: 'lib/browser.js' } },
    { tool: 'repository_read', input: { path: 'lib/launcher.js' } },
    context => ({ tool: 'record', input: { kind: 'finding', text: 'Browser.close() awaits options.browserProcess.close() and then waits with no deadline.',
      dependsOn: Object.values(context.artifacts).filter(value => value.source?.path === 'lib/browser.js').map(value => value.id) } }),
    // The absence claim comes back unsaved, with the unseen code attached.
    context => { returned = context.history.findLast(event => event.event === 'tool-failed');
      assert.equal(returned.code, 'unread-definition'); assert.equal(returned.recoverable, true);
      assert.match(returned.error, /lib\/launcher\.js at offset \d+ \(browserProcess\)/);
      assert.match(returned.error, /close: \(\) => closeOrKill\(DEFAULT_TIMEOUT\)/, 'the code that decides the claim is in the message itself');
      assert.equal(Object.values(context.artifacts).some(value => value.kind === 'finding'), false, 'nothing was saved yet');
      const launcher = Object.values(context.artifacts).find(value => value.source?.path === 'lib/launcher.js');
      return { tool: 'record', input: { kind: 'finding', text: 'Browser.close() awaits options.browserProcess.close(), which is closeOrKill with a deadline; the wait after the kill has no deadline.',
        dependsOn: Object.values(context.artifacts).filter(value => value.kind === 'evidence').map(value => value.id) } }; },
    // A second absence claim naming the same code is not returned: that part has now been shown.
    context => { seenResult = context.history.findLast(event => event.event === 'tool-result').output; return { tool: 'finish', input: { summary: 'Corrected.' } }; },
  ];
  controller = new WorkspaceController({ service, stateDir: join(root, 'client'), config,
    planner: { identity: { model: 'controlled' }, next: async context => { const step = steps[index++]; return typeof step === 'function' ? step(context) : step; } } });
  await controller.restore();
  const { id } = await controller.create({ goal: 'Explain the close stall', repositoryRoot: repository });
  await controller.navigate(id, { pageId: 'main', url: `${ORIGIN}/form` });
  await controller.delegate(id, { pageIds: ['main'], origins: [ORIGIN], actionKinds: ['navigate'], task: 'Explain why close can stall.' });
  await controller.active.get(id)?.done;
  const project = controller.store.get(id);
  assert.equal(project.run.status, 'completed', project.run.detail);
  const launcher = Object.values(project.artifacts).find(value => value.source?.path === 'lib/launcher.js');
  assert.ok(returned, 'the first record was returned');
  const at = LAUNCHER.lastIndexOf('browserProcess = {');
  assert.equal(seenResult.kind, 'finding'); assert.equal(seenResult.unreadMentions, undefined, 'the corrected record raises nothing: the defining code has been shown');
  const findings = Object.values(project.artifacts).filter(value => value.kind === 'finding');
  assert.equal(findings.length, 1); assert.match(findings[0].text, /closeOrKill with a deadline/);
  const finding = findings[0];
  // What the workspace showed is remembered as shown.
  assert.deepEqual(shownRanges(project).get(launcher.id), [[0, SHOWN_AT_FIRST_CHARS], [at - 80, Math.min(LAUNCHER.length, at + 360)]]);
  assert.equal(unreadMentions(project, 'browserProcess.close has no deadline'), null);
  // Pure view of the same case before anything was shown: the assignment, not the bare declaration.
  const fresh = { artifacts: project.artifacts, activity: [] };
  const first = unreadMentions(fresh, 'browserProcess.close has no deadline').mentions[0];
  assert.deepEqual([first.term, first.path, first.offset, first.defines], ['browserProcess', 'lib/launcher.js', at, true]);
  assert.match(first.excerpt, /closeOrKill\(DEFAULT_TIMEOUT\)/);
  // What is left unseen is only the bare declaration's neighbours: nothing worth attaching, so nothing is returned.
  const declared = { artifacts: { x: { id: 'x', kind: 'evidence', revision: 1, source: { kind: 'repository', path: 'lib/x.js', content: `${filler}let browserProcess = void 0;\nuse(browserProcess);\n` } } }, activity: [] };
  const bare = unreadMentions(declared, 'browserProcess.close has no deadline').mentions[0];
  assert.deepEqual([bare.defines, Object.hasOwn(bare, 'excerpt'), bare.offset], [false, false, filler.length + 4], 'a bare declaration is pointed at but not attached');
  // A new revision of the source resets what counts as shown.
  writeFileSync(join(repository, 'lib/launcher.js'), LAUNCHER.replace('DEFAULT_TIMEOUT', 'THIRTY_SECONDS'));
  await controller.checkSources(id);
  assert.equal(unreadMentions(controller.store.get(id), 'browserProcess.close has no deadline').mentions[0].revision, 2);
  // The agent keeps the last word: the same absence claim sent twice is saved the second time.
  index = 0; steps.length = 0;
  const insist = { tool: 'record', input: { kind: 'finding', text: 'browserProcess.close still has no deadline at all.', dependsOn: [finding.id] } };
  steps.push(insist, insist, { tool: 'finish', input: { summary: 'Kept.' } });
  await controller.delegate(id, { pageIds: ['main'], origins: [ORIGIN], actionKinds: ['navigate'], task: 'Record it again.', resume: true });
  await controller.active.get(id)?.done;
  const after = controller.store.get(id);
  assert.equal(Object.values(after.artifacts).filter(value => value.text === insist.input.text).length, 1, 'saved once, on the second send');
  assert.equal(after.activity.filter(event => event.code === 'unread-definition').length, 2, 'one return in each session');
  // Prose with no code names raises nothing, and neither does a short file shown whole.
  assert.equal(unreadMentions(controller.store.get(id), 'Chrome is slow to exit under load.'), null);
  console.log('ok: an absence claim naming code defined in an unseen part of a saved source is returned once with that code attached; shown excerpts and new revisions are tracked; the agent keeps the last word');
} finally {
  controller?.store.close(); await service?.close().catch(() => {});
  rmSync(root, { recursive: true, force: true });
}

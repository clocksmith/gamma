// Investigation memory across a source change: the workspace re-reads saved repository files, marks
// the conclusions that rest on a changed file, says which still hold, keeps rejected explanations on
// the record, and hands the next operator that picture, through the real controller and planner path.
import assert from 'node:assert/strict';
import { mkdtempSync, mkdirSync, readFileSync, writeFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { WorkspaceService } from '../../src/service.js';
import { loadServiceConfig } from '../../src/config.js';
import { WorkspaceController } from '../../src/client/controller.js';
import { InvestigationStore } from '../../src/client/investigation.js';
import { describeChange, validityBrief } from '../../src/client/validity.js';
import { sha256Hex } from '../../src/journal.js';
import { FakeAdapter, ORIGIN } from '../support/fake-adapter.js';

assert.deepEqual(describeChange('a\nb\nc\nd', 'a\nX\nY\nZ\nd'), { beforeLines: 4, afterLines: 5, firstChangedLine: 2, removedLines: 2, addedLines: 3, removedExcerpt: 'b\nc', addedExcerpt: 'X\nY\nZ' });
assert.equal(describeChange('same', 'same').removedLines + describeChange('same', 'same').addedLines, 0);

const config = { ...JSON.parse(readFileSync(new URL('../../config/fawn-workspace-client.json', import.meta.url))), maxTurns: 8 };
const root = mkdtempSync(join(tmpdir(), 'fawn-validity-')), repository = join(root, 'repository');
mkdirSync(join(repository, 'src'), { recursive: true });
const CACHE_V1 = 'export const TTL_SECONDS = 300;\nexport function fresh(entry, now) {\n  return now - entry.storedAt < TTL_SECONDS * 1000;\n}\n';
const CACHE_V2 = 'export const TTL_SECONDS = 900;\nexport function fresh(entry, now) {\n  return entry.pinned || now - entry.storedAt < TTL_SECONDS * 1000;\n}\n';
writeFileSync(join(repository, 'src/cache.js'), CACHE_V1);
writeFileSync(join(repository, 'src/retry.js'), 'export const MAX_ATTEMPTS = 3;\n');
let service, controller;
const open = async planner => {
  service = await WorkspaceService.open({ stateDir: join(root, 'service'), config: loadServiceConfig(), createAdapter: () => new FakeAdapter({ receiptsPath: join(root, 'receipts') }) });
  controller = new WorkspaceController({ service, stateDir: join(root, 'client'), config, planner });
  await controller.restore();
};
try {
  await open(null);
  const { id } = await controller.create({ goal: 'Explain why prices go stale', repositoryRoot: repository });
  await controller.navigate(id, { pageId: 'main', url: `${ORIGIN}/form` });
  const cache = await controller.readRepository(id, { path: 'src/cache.js' }), retry = await controller.readRepository(id, { path: 'src/retry.js' });
  const page = await controller.capture(id, { pageId: 'main' });
  const stale = controller.record(id, { kind: 'finding', text: 'Prices are served from cache for five minutes (TTL_SECONDS = 300).', dependsOn: [cache.id] });
  const retries = controller.record(id, { kind: 'finding', text: 'Failed fetches are retried three times.', dependsOn: [retry.id] });
  const next = controller.record(id, { kind: 'decision', text: 'Next: lower the TTL to 60 seconds.', dependsOn: [stale.id] });
  // Competing explanations are records. Settling one needs a reason and something to rest on.
  assert.throws(() => controller.record(id, { kind: 'hypothesis', text: 'Retries cause it', disposition: { state: 'rejected', reason: 'no' } }), /needs a reason and at least one record/);
  assert.throws(() => controller.record(id, { kind: 'hypothesis', text: 'x', dependsOn: [retry.id], disposition: { state: 'rejected', reason: ' ' } }), /needs a reason/);
  assert.throws(() => controller.record(id, { kind: 'hypothesis', text: 'x', disposition: { state: 'maybe' } }), /open, supported, rejected/);
  assert.throws(() => controller.record(id, { kind: 'finding', text: 'x', disposition: { state: 'open' } }), /Only a hypothesis/);
  const open1 = controller.record(id, { kind: 'hypothesis', text: 'The pricing service itself returns old prices.' });
  assert.deepEqual(open1.disposition, { state: 'open', reason: '' });
  const rejected = controller.record(id, { kind: 'hypothesis', text: 'Retries replay an old response.', dependsOn: [retry.id],
    disposition: { state: 'rejected', reason: 'retry.js only repeats the request; it keeps no response.' } });

  // Nothing changed yet: everything recorded still holds, and the rejected explanation stays listed.
  let brief = await controller.checkSources(id);
  assert.deepEqual([brief.changedSources.length, brief.needsRecheck.length, brief.unchangedSourceCount], [0, 0, 2]);
  assert.deepEqual(brief.uncheckedSources.map(entry => entry.artifactId), [page.id], 'a page is not silently treated as rechecked');
  assert.deepEqual(brief.stillValid.map(entry => entry.id).sort(), [stale.id, retries.id, next.id, open1.id].sort());
  assert.deepEqual(brief.rejectedHypotheses.map(entry => [entry.id, entry.reason]), [[rejected.id, 'retry.js only repeats the request; it keeps no response.']]);
  assert.match(brief.nextAction, new RegExp(`open hypothesis ${open1.id}`));

  // The file changes underneath the investigation.
  writeFileSync(join(repository, 'src/cache.js'), CACHE_V2);
  brief = await controller.checkSources(id);
  assert.equal(brief.changedSources.length, 1);
  const change = brief.changedSources[0];
  assert.deepEqual([change.path, change.previousRevision, change.revision, change.refreshed], ['src/cache.js', 1, 2, true]);
  assert.deepEqual([change.change.firstChangedLine, change.change.removedLines, change.change.addedLines], [1, 3, 3]);
  assert.match(change.change.addedExcerpt, /TTL_SECONDS = 900/);
  assert.deepEqual(change.affects.sort(), [stale.id, next.id].sort(), 'the brief names the records resting on the changed file');
  const recheck = Object.fromEntries(brief.needsRecheck.map(entry => [entry.id, entry]));
  assert.deepEqual(Object.keys(recheck).sort(), [stale.id, next.id].sort());
  assert.deepEqual(recheck[stale.id].because.map(cause => [cause.what, cause.reason, cause.recordedAtRevision, cause.currentRevision]), [['src/cache.js', 'source changed since this was recorded', 1, 2]]);
  assert.deepEqual(recheck[next.id].because.map(cause => cause.reason), ['itself needs rechecking']);
  assert.deepEqual(brief.stillValid.map(entry => entry.id).sort(), [retries.id, open1.id].sort(), 'records resting on unchanged sources still hold');
  assert.match(brief.nextAction, /Recheck 2 record\(s\)/);
  let project = controller.store.get(id);
  assert.equal(project.artifacts[cache.id].source.content, CACHE_V2, 'the evidence record now carries the current bytes');
  assert.equal(project.artifacts[cache.id].source.sha256, sha256Hex(CACHE_V2));
  assert.ok(readFileSync(join(root, 'client/investigations/investigation.jsonl'), 'utf8').includes('TTL_SECONDS = 300'), 'the earlier bytes stay in the journal');
  // Checking again reports nothing new and does not create another revision.
  assert.equal((await controller.checkSources(id)).changedSources.length, 0);
  assert.equal(controller.store.get(id).artifacts[cache.id].revision, 2);
  controller.store.close(); await service.close();

  // A different agent resumes. The workspace checks sources before it reads anything; the handoff
  // carries what needs rechecking, and the agent corrects one record and confirms the other.
  const seen = [];
  const steps = [
    context => { const validity = context.handoff.validity;
      assert.deepEqual(validity.needsRecheck.map(entry => entry.id).sort(), [stale.id, next.id].sort());
      assert.deepEqual(validity.rejectedHypotheses.map(entry => entry.id), [rejected.id]);
      return { tool: 'record', input: { id: stale.id, expectedRevision: 1, kind: 'finding', text: 'Prices are served from cache for fifteen minutes (TTL_SECONDS = 900), and pinned entries never expire.', dependsOn: [cache.id] } }; },
    () => ({ tool: 'record', input: { id: next.id, expectedRevision: 1, kind: 'decision', text: 'Next: remove the pinned bypass, then lower the TTL.', dependsOn: [stale.id] } }),
    () => ({ tool: 'record', input: { id: open1.id, expectedRevision: 1, kind: 'hypothesis', text: 'The pricing service itself returns old prices.', dependsOn: [cache.id],
      disposition: { state: 'rejected', reason: 'cache.js alone explains fifteen-minute staleness.' } } }),
    () => ({ tool: 'sources_check', input: {} }),
    context => { const checked = context.history.findLast(event => event.event === 'tool-result' && event.output?.nextAction)?.output;
      assert.deepEqual([checked.needsRecheck.length, checked.changedSources.length], [0, 0]);
      assert.deepEqual(checked.rejectedHypotheses.map(entry => entry.id).sort(), [rejected.id, open1.id].sort());
      return { tool: 'finish', input: { summary: 'Rechecked against the changed cache code.' } }; },
  ];
  let turn = 0;
  await open({ identity: { model: 'scripted-resuming-agent' }, next: async context => { seen.push(context); return steps[turn++](context); } });
  await controller.navigate(id, { pageId: 'main', url: `${ORIGIN}/form` });
  await controller.delegate(id, { pageIds: ['main'], origins: [ORIGIN], actionKinds: ['navigate'], task: 'Continue the investigation.', resume: true });
  await controller.active.get(id)?.done;
  project = controller.store.get(id);
  assert.equal(project.run.status, 'completed', JSON.stringify(project.run));
  assert.deepEqual(project.activity.filter(event => event.event === 'tool-failed').map(event => event.error), []);
  assert.deepEqual([stale.id, next.id, open1.id].map(key => [project.artifacts[key].status, project.artifacts[key].revision]), [['current', 2], ['current', 2], ['current', 2]]);
  assert.match(project.artifacts[stale.id].text, /fifteen minutes/);
  assert.equal(seen[0].handoff.validity.changedSources.length, 0, 'the change was already recorded; resume found nothing newer');

  // A source that can no longer be read keeps its saved copy, and what rests on it is flagged.
  await controller.takeOver(id);
  rmSync(join(repository, 'src/retry.js'));
  brief = await controller.checkSources(id);
  assert.deepEqual(brief.changedSources.map(entry => [entry.path, entry.missing]), [['src/retry.js', true]]);
  assert.deepEqual(brief.needsRecheck.map(entry => entry.id).sort(), [retries.id, rejected.id].sort());
  assert.ok(brief.needsRecheck.every(entry => entry.because.some(cause => cause.reason === 'source could not be re-read')));
  assert.equal(controller.store.get(id).artifacts[retry.id].revision, 1, 'the saved copy is kept, not overwritten');
  controller.store.close(); await service.close();

  // The picture survives a restart: it is rebuilt from the journal alone.
  const reopened = new InvestigationStore(join(root, 'client/investigations'));
  const again = validityBrief(reopened.get(id));
  assert.deepEqual(again.needsRecheck.map(entry => entry.id).sort(), [retries.id, rejected.id].sort());
  assert.deepEqual(again.rejectedHypotheses.length, 2);
  reopened.close();
  service = null; controller = null;

  // The brief rides in every handoff, so it stays bounded however large the investigation grows.
  {
    const many = { run: null, activity: [], artifacts: Object.fromEntries(Array.from({ length: 300 }, (_, index) => [`r${index}`,
      { id: `r${index}`, kind: index % 2 ? 'finding' : 'question', status: index % 3 ? 'current' : 'needs-review', revision: 1, text: 'long '.repeat(400), dependsOn: [] }])) };
    const large = validityBrief(many);
    assert.ok(JSON.stringify(large).length < 12000, `bounded brief, got ${JSON.stringify(large).length}`);
    assert.deepEqual([large.counts.needsRecheck, large.needsRecheck.length, large.omitted.needsRecheck], [100, 20, 80]);
    assert.deepEqual([large.counts.stillValid, large.stillValid.length, large.omitted.stillValid], [200, 12, 188]);
  }
  console.log('ok: source changes mark dependent conclusions, unchanged ones still hold, rejected hypotheses persist, a resuming agent rechecks through the planner path, lost sources are flagged, and the brief survives restart');
} finally {
  await controller?.close().catch(() => {}); await service?.close().catch(() => {});
  rmSync(root, { recursive: true, force: true });
}

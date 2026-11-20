// Long investigations must remain resumable without sending every saved byte at once.
import assert from 'node:assert/strict';
import { mkdtempSync, readFileSync, rmSync } from 'node:fs';
import { join } from 'node:path';
import { tmpdir } from 'node:os';
import { WorkspaceController } from '../../src/client/controller.js';
import { WorkspaceService } from '../../src/service.js';
import { loadServiceConfig } from '../../src/config.js';
import { investigationContext } from '../../src/client/agent.js';
import { artifactMemory, listArtifacts } from '../../src/client/artifact-memory.js';
import { sha256Hex } from '../../src/journal.js';
import { FakeAdapter, ORIGIN } from '../support/fake-adapter.js';
const root = mkdtempSync(join(tmpdir(), 'fawn-artifact-memory-'));
const config = { ...JSON.parse(readFileSync(new URL('../../config/fawn-workspace-client.json', import.meta.url))), maxTurns: 5, maxInputBytes: 80000 };
let service, controller;
try {
  service = await WorkspaceService.open({ stateDir: join(root, 'service'), config: loadServiceConfig(),
    createAdapter: () => new FakeAdapter({ receiptsPath: join(root, 'receipts') }) });
  controller = new WorkspaceController({ service, stateDir: join(root, 'client'), config });
  const { id } = await controller.create({ goal: 'Continue a long investigation from its saved evidence.' });
  await controller.navigate(id, { pageId: 'main', url: `${ORIGIN}/form` });
  const needle = 'archived.target+[sentinel]';
  const shared = new Set();
  for (let index = 0; index < 50; index++) {
    const content = `source ${index}: ` + 'saved evidence '.repeat(1000) + (index === 0 ? needle : 'unrelated ending');
    const artifact = controller.store.revise(id, { id: `source-${index}`, kind: 'evidence', text: `Saved source ${index}`,
      source: { content, sha256: sha256Hex(content), path: `source-${index}.txt` } });
    shared.add(artifact.id);
    controller.store.activity(id, { event: 'tool-result', callId: `capture-${index}`, output: artifact });
  }
  const privateRecord = controller.store.revise(id, { kind: 'finding', text: 'private unshared marker' });
  const project = controller.store.get(id), original = JSON.stringify(project);
  const context = investigationContext(project, { task: 'Find the old result', permissions: {}, initialArtifacts: shared,
    startSequence: 0, shareRecords: true, visibleArtifacts: shared });
  assert.equal(context.artifactCatalog.total, 50);
  assert.equal(Object.keys(context.artifacts).length, 8);
  assert.ok(Buffer.byteLength(JSON.stringify(context)) < config.maxInputBytes, 'Even historical tool results cannot reload omitted evidence');
  assert.equal(listArtifacts(project, { query: 'private unshared marker' }, shared).total, 0);
  const seen = []; let after = null;
  do { const result = listArtifacts(project, { after }, shared); assert.ok(result.entries.length <= 12);
    seen.push(...result.entries.map(value => value.id)); after = result.nextCursor; } while (after !== null);
  assert.equal(new Set(seen).size, 50); assert.equal(seen.length, 50);
  assert.equal(JSON.stringify(project), original, 'Catalog and context never mutate the saved record');
  assert.equal(artifactMemory(project, new Set()).artifactCatalog.total, 0);
  assert.throws(() => listArtifacts(project, { after: privateRecord.id }, shared), /cursor/);

  // A new delegation starts within budget, searches old bytes, then retrieves the exact omitted source.
  let step = 0, entry, excerpt;
  controller.planner = { identity: { model: 'controlled-memory-reader' }, next: async context => {
    assert.ok(Buffer.byteLength(JSON.stringify(context)) < config.maxInputBytes);
    if (step++ === 0) return { tool: 'artifact_list', input: { query: needle } };
    if (step === 2) { entry = context.history.findLast(event => event.event === 'tool-result').output.entries[0];
      assert.equal(entry.match.field, 'source');
      return { tool: 'artifact_read', input: { artifactId: entry.id, expectedRevision: entry.revision,
        field: entry.match.field, offset: entry.match.offset } }; }
    excerpt = context.history.findLast(event => event.event === 'tool-result').output;
    return { tool: 'finish', input: { summary: 'The archived source was retrieved.' } };
  } };
  await controller.delegate(id, { pageIds: ['main'], origins: [ORIGIN], actionKinds: ['fill'], task: 'Find the archived target', shareRecords: true });
  await controller.active.get(id)?.done;
  assert.equal(controller.store.get(id).run.status, 'completed');
  assert.equal(entry.id, 'source-0'); assert.ok(excerpt.content.includes(needle));
  assert.equal(excerpt.sourceSha256, project.artifacts['source-0'].source.sha256);
  console.log('ok: fifty saved sources stay within context budget; complete paged search and exact omitted-evidence retrieval');
} finally { await controller?.close(); await service?.close(); rmSync(root, { recursive: true, force: true }); }

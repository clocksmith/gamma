// Returning agents can inspect evidence tails without wider disclosure or live reads.
import assert from 'node:assert/strict';
import { mkdtempSync, readFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { readArtifact, MAX_ARTIFACT_READ_CHARS } from '../../src/client/artifact-read.js';
import { investigationContext } from '../../src/client/agent.js';
import { WorkspaceController } from '../../src/client/controller.js';
import { WorkspaceService } from '../../src/service.js';
import { loadServiceConfig } from '../../src/config.js';
import { sha256Hex } from '../../src/journal.js';
import { FakeAdapter, ORIGIN } from '../support/fake-adapter.js';

const directory = mkdtempSync(join(tmpdir(), 'fawn-artifact-read-'));
const config = { ...JSON.parse(readFileSync(new URL('../../config/fawn-workspace-client.json', import.meta.url))), maxTurns: 4 };
let service, controller;
try {
  service = await WorkspaceService.open({ stateDir: join(directory, 'service'), config: loadServiceConfig(),
    createAdapter: () => new FakeAdapter({ receiptsPath: join(directory, 'receipts') }) });
  controller = new WorkspaceController({ service, stateDir: join(directory, 'client'), config });
  const { id } = await controller.create({ goal: 'Read the conclusion of saved evidence' });
  await controller.navigate(id, { pageId: 'main', url: ORIGIN + '/form' });
  const content = 'earlier evidence\n'.repeat(800) + 'TAIL: the acknowledgement may be lost after commit.';
  const evidence = controller.store.revise(id, { kind: 'evidence', text: 'Long captured evidence',
    source: { content, sha256: sha256Hex(content) } });
  const project = controller.store.get(id), visible = new Set([evidence.id]);
  const context = investigationContext(project, { task: 'Read saved bytes', permissions: {}, initialArtifacts: visible,
    startSequence: 0, shareRecords: true, visibleArtifacts: visible });
  assert.ok(!context.artifacts[evidence.id].source.content.includes('TAIL:'));
  assert.equal(context.artifacts[evidence.id].source.contentTruncated.totalChars, content.length);
  const chunks = [];
  let offset = 0;
  do {
    const result = readArtifact(project, { artifactId: evidence.id, expectedRevision: evidence.revision, offset }, visible);
    assert.ok(result.content.length <= MAX_ARTIFACT_READ_CHARS);
    assert.equal(result.sliceSha256, sha256Hex(result.content));
    assert.equal(result.sourceSha256, evidence.source.sha256);
    chunks.push(result.content); offset = result.nextOffset;
  } while (offset !== null);
  assert.equal(chunks.join(''), content);
  for (const input of [
    { expectedRevision: 0 }, { expectedRevision: 2 }, { expectedRevision: undefined },
    { expectedRevision: 1, offset: -1 }, { expectedRevision: 1, offset: content.length + 1 },
    { expectedRevision: 1, maxChars: 6001 }, { expectedRevision: 1, maxChars: 0 },
  ]) assert.throws(() => readArtifact(project, { artifactId: evidence.id, ...input }, visible));
  for (const input of [{ offset: -1 }, { offset: content.length + 1 }, { maxChars: 6001 }, { maxChars: 0 }, { expectedRevision: 99 }]) {
    assert.throws(() => readArtifact(project, { artifactId: evidence.id, expectedRevision: 1, ...input }, visible));
  }
  assert.throws(() => readArtifact(project, { artifactId: evidence.id, expectedRevision: 1 }, new Set()), /not shared/);
  assert.throws(() => readArtifact(project, { artifactId: evidence.id, expectedRevision: 1 }, null), /not shared/);

  // Exercise actual delegation/context routing, including explicit disclosure consent.
  let turn = 0, tail;
  controller.planner = { identity: { model: 'controlled-artifact-reader' }, next: async context => {
    if (turn++ === 0) return { tool: 'artifact_read', input: { artifactId: evidence.id, expectedRevision: 1, offset: content.length - 52 } };
    tail = context.history.findLast(event => event.event === 'tool-result').output;
    return { tool: 'finish', input: { summary: 'The stored source explains acknowledgement loss.' } };
  } };
  await controller.delegate(id, { pageIds: ['main'], origins: [ORIGIN], actionKinds: ['fill'], task: 'Read the saved conclusion', shareRecords: true });
  await controller.active.get(id)?.done;
  assert.equal(controller.store.get(id).run.status, 'completed');
  assert.ok(tail.content.includes('TAIL:'));
  assert.equal(tail.sourceSha256, evidence.source.sha256);
  controller.planner = { identity: {}, next: async () => ({ tool: 'artifact_read', input: { artifactId: evidence.id, expectedRevision: 1 } }) };
  await controller.delegate(id, { pageIds: ['main'], origins: [ORIGIN], actionKinds: ['fill'], task: 'New task with no saved-record consent' });
  await controller.active.get(id)?.done;
  assert.match(controller.store.get(id).run.detail, /not shared/);
  console.log('ok: bounded complete saved-evidence reads, revision binding, exact hashes and delegation disclosure');
} finally { await controller?.close(); await service?.close(); rmSync(directory, { recursive: true, force: true }); }

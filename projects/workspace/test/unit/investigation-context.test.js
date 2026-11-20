import assert from 'node:assert/strict';
import { investigationContext } from '../../src/client/agent.js';
const source = 'The request can commit before the response arrives.';
const artifact = { id: 'source-1', kind: 'evidence', source: { content: source } };
const project = { goal: 'Trace a retry', repositoryRoot: '/selected/repository', artifacts: { 'source-1': artifact }, activity: [
  { seq: 1, event: 'planner-result', usage: { privateBookkeeping: 'do not send'.repeat(1000) } },
  { seq: 2, type: 'run-updated', run: { usage: ['accounting only'] } },
  { seq: 3, event: 'tool-requested', callId: 'call-1', tool: 'capture', input: { pageId: 'main' } },
  { seq: 4, event: 'tool-result', callId: 'call-1', output: artifact }
] };
const options = { task: 'Inspect', permissions: { pageIds: ['main'] }, initialArtifacts: new Set(), startSequence: 0, shareRecords: false };
const before = JSON.stringify(project);
const context = investigationContext(project, options), encoded = JSON.stringify(context);
assert.equal(encoded.split(source).length - 1, 1, 'Saved evidence should appear once in planner context');
assert.ok(!encoded.includes('privateBookkeeping'));
assert.ok(!encoded.includes('/selected/repository'));
assert.equal(context.history.length, 2);
assert.equal(context.history[1].output.artifactId, 'source-1');
assert.equal(JSON.stringify(project), before, 'Context compaction must preserve the complete audit trail');
const hidden = investigationContext(project, { ...options, startSequence: 4, initialArtifacts: new Set(['source-1']) });
assert.ok(!JSON.stringify(hidden).includes(source));
assert.equal(investigationContext(project, { ...options, shareRecords: true, initialArtifacts: new Set(['source-1']) }).artifacts['source-1'].source.content, source);
const isolated = investigationContext(project, { ...options, shareRecords: true, visibleArtifacts: new Set() });
assert.ok(!JSON.stringify(isolated.artifacts).includes(source), 'Explicit record selection overrides broad historical context');
console.log('ok: compact planner context retains evidence once, isolates bookkeeping and requires consent for saved sources');

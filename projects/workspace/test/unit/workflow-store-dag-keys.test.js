// Regression: v3 TraceDag exports may carry entryRoots (multi-entry DAGs). The workflow store,
// TraceDag.restore and workflow-store.schema.json must accept the same optional key set.
import assert from 'node:assert/strict';
import { mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import test from 'node:test';
import { WorkflowStore } from '../../src/client/workflow-store.js';
import { TraceDag, TRACE_DAG_OPTIONAL_KEYS } from '../../src/client/trace-dag.js';

const limits = { maxNodes: 32, maxEdges: 32, maxSteps: 8 };
const scope = { accountScope: 'account-a', template: 'multi-entry-form' };
const schema = JSON.parse(readFileSync(new URL('../../workflow-store.schema.json', import.meta.url), 'utf8'));
const dagSchema = schema.properties.workflowVersions.additionalProperties.properties.dag;

// A -> B -> T with B also taught as an entry. Default roots are {A}, so export() emits entryRoots.
function multiEntryDag(key) {
  const shape = new TraceDag(limits);
  if (key) shape.key = key;
  const id = name => shape.hash(['node', name]);
  const click = name => ({ kind: 'click', locator: shape.hash(['locator', name]), slot: null });
  const [a, b, t] = ['a', 'b', 't'].map(id);
  const dag = TraceDag.restore({ version: 3, key: shape.key, limits, entryRoots: [a, b], nodes: [
    [a, { depth: 0, edges: [{ next: b, step: click('one') }], repairs: [], terminal: false }],
    [b, { depth: 1, edges: [{ next: t, step: click('two') }], repairs: [], terminal: false }],
    [t, { depth: 2, edges: [], repairs: [], terminal: true }],
  ] }, limits).export();
  assert.deepEqual(dag.entryRoots, [a, b].sort());
  return dag;
}

function newStore(directory, sync = null) {
  return new WorkflowStore({ directory, ownerScope: 'person-a', limits, maxBytes: 100000,
    lockWaitMs: 200, lockRetryMs: 5, sync });
}

test('schema dag optional keys equal the code allowlist', () => {
  const required = new Set(dagSchema.required);
  const optional = Object.keys(dagSchema.properties).filter(key => !required.has(key)).sort();
  assert.deepEqual(optional, [...TRACE_DAG_OPTIONAL_KEYS].sort());
  assert.ok(TRACE_DAG_OPTIONAL_KEYS.includes('entryRoots'));
  assert.equal(dagSchema.additionalProperties, false);
});

test('WorkflowStore reads a stored multi-entry DAG with entryRoots', async () => {
  const root = mkdtempSync(join(tmpdir(), 'workflow-store-dag-keys-'));
  try {
    const store = newStore(join(root, 'cache'));
    const empty = await store.checkout(scope);
    const state = JSON.parse(readFileSync(store.path, 'utf8'));
    state.workflowVersions[empty.versionId].dag = multiEntryDag(empty.dag.key);
    writeFileSync(store.path, JSON.stringify(state), { mode: 0o600 });
    const read = await store.checkout(scope);
    assert.deepEqual(read.dag.entryRoots, state.workflowVersions[empty.versionId].dag.entryRoots);
    assert.equal(store.summary(scope).hasLearnedGraph, true);
  } finally { rmSync(root, { recursive: true, force: true }); }
});

test('WorkflowStore publishes a merged multi-entry DAG from sync', async () => {
  const root = mkdtempSync(join(tmpdir(), 'workflow-store-dag-keys-'));
  const key = new TraceDag(limits).key;
  const remote = multiEntryDag(key);
  const sync = {
    ownerScope: 'person-a',
    empty: () => { const dag = new TraceDag(limits); dag.key = key; return dag.export(); },
    version: () => 'v',
    exchange: async () => ({ dag: remote, revision: 1 }),
  };
  try {
    const store = newStore(join(root, 'cache'), sync);
    assert.deepEqual(await store.synchronize(scope), { status: 'synced', revision: 1 });
    const merged = await store.checkout(scope);
    assert.equal(merged.revision, 1);
    assert.deepEqual(merged.dag.entryRoots, remote.entryRoots);
  } finally { rmSync(root, { recursive: true, force: true }); }
});

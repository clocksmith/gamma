// A downstream edit must not turn an unreviewed premise into current evidence.
import assert from 'node:assert/strict';
import { mkdtempSync, readFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { InvestigationStore } from '../../src/client/investigation.js';
import { canonicalJson, sha256Hex } from '../../src/journal.js';

const directory = mkdtempSync(join(tmpdir(), 'fawn-investigation-dependencies-'));
let store;
try {
  store = new InvestigationStore(directory);
  const id = 'evidence-review';
  store.create({ id, goal: 'Choose an implementation from the current source evidence.' });
  const source = text => ({ kind: 'repository', path: 'implementation.js', content: text, sha256: sha256Hex(text) });
  const evidence = store.revise(id, { id: 'source', kind: 'evidence', text: 'Original implementation', source: source('old implementation') });
  const finding = store.revise(id, { id: 'finding', kind: 'finding', text: 'The implementation supports the decision', dependsOn: [evidence.id] });
  const decision = store.revise(id, { id: 'decision', kind: 'decision', text: 'Use this implementation', dependsOn: [finding.id] });
  store.revise(id, { id: evidence.id, expectedRevision: evidence.revision, kind: 'evidence', text: 'Changed implementation', source: source('changed implementation') });
  assert.equal(store.get(id).artifacts[finding.id].status, 'needs-review');

  const premature = store.revise(id, { id: decision.id, expectedRevision: decision.revision,
    kind: 'decision', text: 'Edited wording still relies on the unreviewed finding', dependsOn: [finding.id] });
  assert.equal(premature.status, 'needs-review', 'Editing a conclusion cannot revalidate its stale premise');
  const followup = store.revise(id, { id: 'followup', kind: 'question', text: 'What does this imply?', dependsOn: [premature.id] });
  assert.equal(followup.status, 'needs-review', 'New dependents also retain the unresolved review requirement');

  store.close(); store = new InvestigationStore(directory);
  assert.equal(store.get(id).artifacts[decision.id].status, 'needs-review', 'The requirement survives restart');
  assert.equal(store.get(id).artifacts[followup.id].status, 'needs-review');

  const reviewed = store.revise(id, { id: finding.id, expectedRevision: finding.revision,
    kind: 'finding', text: 'Reviewed against the changed source', dependsOn: [evidence.id] });
  assert.equal(reviewed.status, 'current');
  assert.equal(store.get(id).artifacts[decision.id].status, 'needs-review', 'Reviewing a premise does not silently approve an old decision');
  const repaired = store.revise(id, { id: decision.id, expectedRevision: premature.revision,
    kind: 'decision', text: 'Reviewed against the current finding', dependsOn: [finding.id] });
  assert.equal(repaired.status, 'current');
  assert.equal(repaired.dependencyRevisions[finding.id], reviewed.revision);
  assert.equal(store.get(id).artifacts[followup.id].status, 'needs-review');

  const independent = store.revise(id, { id: followup.id, expectedRevision: followup.revision,
    kind: 'question', text: 'Independent question with no stale premise', dependsOn: [] });
  assert.equal(independent.status, 'current', 'Explicitly removing an obsolete dependency is supported');
  store.close(); store = new InvestigationStore(directory);
  assert.equal(store.get(id).artifacts[decision.id].status, 'current');
  assert.equal(store.get(id).artifacts[followup.id].status, 'current');
  store.revise(id, { id: evidence.id, kind: 'evidence', text: 'Source changed again',
    source: { content: 'third revision', sha256: sha256Hex('third revision') }, expectedRevision: 2 });

  // Simulate a valid pre-fix journal entry, whose stored status claimed current.
  // Replay repairs the derived view without changing historical bytes or hashes.
  const { status, contentHash, ...previousRevision } = repaired;
  const legacyRevision = { ...previousRevision, text: 'Old client approved a stale premise', revision: repaired.revision + 1 };
  store.journal.append('artifact-revised', { projectId: id,
    artifact: { ...legacyRevision, status: 'current', contentHash: sha256Hex(canonicalJson(legacyRevision)) } });
  store.close();
  const journalPath = join(directory, 'investigation.jsonl');
  const savedBytes = readFileSync(journalPath);
  store = new InvestigationStore(directory);
  assert.equal(store.get(id).artifacts[decision.id].status, 'needs-review');
  assert.deepEqual(readFileSync(journalPath), savedBytes);
  console.log('ok: stale premises survive edits/restarts, valid review repairs the dependency chain');
} finally { store?.close(); rmSync(directory, { recursive: true, force: true }); }

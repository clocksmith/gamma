import assert from 'node:assert/strict';
import { judgeHandoff, repostCheck } from '../../qualification/real-handoff-judge.js';
import { sha256Hex } from '../../src/journal.js';
const docsUrl = 'https://docs.example/pattern/combobox/', trackerUrl = 'https://tracker.example/issues/17';
const repositoryFiles = ['choice.js', 'cases.md'];
function project() {
  const artifacts = {};
  for (const [id, source] of [['page', { kind: 'page', url: docsUrl }], ['code', { kind: 'repository', path: 'choice.js' }], ['case', { kind: 'repository', path: 'cases.md' }]]) {
    artifacts[id] = { id, kind: 'evidence', status: 'current', source: { ...source, content: id, sha256: sha256Hex(id) } };
  }
  artifacts.finding = { id: 'finding', kind: 'finding', status: 'current', text: 'The custom combobox changes its visual option without committing the selected value to application state. Inspect the input and selection event path.', dependsOn: ['page', 'code', 'case'] };
  artifacts.question = { kind: 'question', status: 'current', text: 'Which selection event is consumed?' };
  artifacts.decision = { kind: 'decision', status: 'current', text: 'Trace the selected-value event handler next.' };
  return { artifacts, run: { status: 'completed' } };
}
const p = project(), text = p.artifacts.finding.text;
const grade = (value = p, tracker = { commits: 1, comments: [text] }) => judgeHandoff(value, { tracker, docsUrl, repositoryFiles, repostBeforeEstablishing: false });
assert.equal(grade().accepted, true);
assert.equal(grade(p, { commits: 1, comments: ['An unrelated comment.'] }).accepted, false);
assert.equal(grade(p, { commits: 1, comments: [text.slice(0, 60) + ' unrelated conclusion'] }).accepted, false);
assert.equal(grade(p, { commits: 2, comments: [text, text] }).accepted, false);
assert.equal(grade(p, { commits: 1, comments: ['  ' + text.replace(/ /g, '\n') + '  '] }).accepted, true);
for (const alter of [
  value => { value.run.status = 'needs-attention'; },
  value => { value.artifacts.page.source.url = 'https://docs.example/unrelated'; },
  value => { value.artifacts.finding.status = 'needs-review'; },
  value => { value.artifacts.question.status = 'needs-review'; },
  value => { value.artifacts.code.source.content = 'tampered'; },
  value => { delete value.artifacts.case; },
]) { const value = project(); alter(value); assert.equal(grade(value).accepted, false); }
const options = { trackerPageId: 'tracker', trackerUrl };
const request = (seq, callId, tool, input) => ({ seq, event: 'tool-requested', callId, tool, input });
const result = (seq, callId, output) => ({ seq, event: 'tool-result', callId, output });
const post = request(10, 'post', 'act', { pageId: 'tracker', kind: 'submit', effect: { effectKey: 'tracker-comment' } });
for (const inspection of [
  [request(3, 'look', 'observe', { pageId: 'main' }), result(4, 'look', { pageId: 'main', url: docsUrl, text: 'docs' })],
  [request(3, 'look', 'observe', { pageId: 'tracker' })],
  [request(3, 'look', 'observe', { pageId: 'tracker' }), result(4, 'look', { error: 'failed', pageId: 'tracker', url: trackerUrl, text: '' })],
  [request(3, 'look', 'observe', { pageId: 'tracker' }), result(4, 'look', { pageId: 'tracker', url: docsUrl, text: 'wrong document' })],
  [request(3, 'rec', 'reconcile', { actionId: 'unknown' }), result(4, 'rec', { actionId: 'unknown', reconciliation: { result: 'effect-present' } })],
]) assert.equal(repostCheck([...inspection, post], 2, options), true);
const looked = [request(3, 'look', 'observe', { pageId: 'tracker' }), result(4, 'look', { pageId: 'tracker', url: trackerUrl, text })];
assert.equal(repostCheck([...looked, post], 2, options), false);
assert.equal(repostCheck([...looked, post], 5, options), true, 'inspection predating resume does not establish what the returning agent checked');
const oldPost = request(1, 'earlier-post', 'act', { pageId: 'tracker', kind: 'submit', effect: { effectKey: 'tracker-comment' } });
const reconcile = request(3, 'rec', 'reconcile', { actionId: 'earlier-post' });
assert.equal(repostCheck([oldPost, reconcile, result(4, 'rec', { actionId: 'earlier-post', reconciliation: { result: 'effect-absent' } }), post], 2, options), false);
assert.equal(repostCheck([oldPost, reconcile, result(4, 'rec', { actionId: 'earlier-post', reconciliation: { result: 'inconclusive' } }), post], 2, options), true);
assert.equal(repostCheck([request(3, 'docs-look', 'observe', { pageId: 'main' }), result(4, 'docs-look', { pageId: 'main', url: docsUrl, text: 'docs' }), request(10, 'docs-click', 'act', { pageId: 'main', kind: 'click' })], 2, options), false);
assert.equal(repostCheck([request(3, 'nav', 'act', { pageId: 'main', kind: 'navigate', target: { url: trackerUrl } }), request(10, 'post-main', 'act', { pageId: 'main', kind: 'submit' })], 2, options), true, 'moving the tracker into another tab does not evade inspection');
console.log('ok: matching finding post and successful tracker-specific inspection required');

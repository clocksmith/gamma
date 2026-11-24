import assert from 'node:assert/strict';
import test from 'node:test';
import { OBSERVATION_SCHEMA, branchExpression, decideBranch, parseBranchResult, verifyBranches } from '../../src/client/branch-verifier.js';

const page = (change = {}) => {
  const dirty = change.dirty ?? [];
  return { alerts: [], statuses: [], truncated: false, ...change, dirty, values: change.values ?? dirty.map(name => [name, 'digest']) };
};
const branch = ({ ended = 'finished', attempts = [], after = {}, before = {}, thrown = null, ok = true, value } = {}) => [ended,
  ...attempts.map(([attempt, target]) => JSON.stringify({ attempt, target })),
  ...(ended === 'finished' ? [JSON.stringify({ ok, value: value ?? { schema: OBSERVATION_SCHEMA, before: page(before), after: page(after), thrown } })] : [])].join('\n');
const write = ['form', 'https://app.test/items/7/save'];
const expect = { attempt: write[0], target: write[1] };
const control = branch();
const candidate = (id, options = {}, extra = {}) => ({ id, text: branch({ attempts: [write], ...options }), expect, ...extra });
const verdicts = result => Object.fromEntries(result.rows.map(row => [row.id, row.verdict]));

test('parses the browser result format and fails closed on damaged output', () => {
  assert.deepEqual(parseBranchResult('finished\n{"attempt":"fetch","target":"https://a.test/"}\n{"ok":true,"value":1}\n'),
    { ended: 'finished', attempts: [{ attempt: 'fetch', target: 'https://a.test/' }], result: { ok: true, value: 1 } });
  assert.equal(parseBranchResult('finished\nnot json').ended, 'malformed');
  assert.equal(parseBranchResult('finished\n{"ok":true}\n{"ok":true}').ended, 'malformed');
  assert.equal(parseBranchResult(null).ended, 'malformed');
});

test('sends one clean candidate to review after exactly one prerequisite read', async () => {
  let reads = 0;
  const result = await decideBranch({ control, candidates: [candidate('a')], attest: async ({ winner }) => { reads += 1; assert.equal(winner, 'a'); return { holds: true, facts: 'v1' }; } });
  assert.equal(result.decision, 'review');
  assert.equal(result.winner, 'a');
  assert.equal(result.facts, 'v1');
  assert.equal(reads, 1);
});

test('a hidden second write or a different target is rejected', () => {
  const result = verifyBranches({ control, candidates: [
    candidate('extra', { attempts: [write, ['fetch', 'https://app.test/items/7/delete']] }),
    candidate('elsewhere', { attempts: [['form', 'https://app.test/items/8/save']] }),
  ] });
  assert.equal(result.decision, 'abstain');
  assert.deepEqual(verdicts(result), { extra: 'unexpected-effect', elsewhere: 'unexpected-effect' });
});

test('only exact attempts seen in the no-op control are ambient', () => {
  const ping = ['beacon', 'https://metrics.test/ping'];
  const noisy = branch({ attempts: [ping] });
  assert.equal(verifyBranches({ control: noisy, candidates: [candidate('a', { attempts: [ping, write] })] }).winner, 'a');
  assert.deepEqual(verdicts(verifyBranches({ control: noisy, candidates: [candidate('twice', { attempts: [ping, ping, write] })] })), { twice: 'unexpected-effect' });
});

test('branches without a usable result are not treated as success', () => {
  const result = verifyBranches({ control, candidates: [
    { id: 'cancelled', text: branch({ ended: 'cancelled' }), expect },
    { id: 'failed', text: branch({ attempts: [write], ok: false, value: 'SyntaxError' }), expect },
    { id: 'foreign', text: branch({ attempts: [write], value: { schema: 'other' } }), expect },
    candidate('nothing', { attempts: [] }),
  ] });
  assert.deepEqual(verdicts(result), { cancelled: 'no-result', failed: 'no-result', foreign: 'no-result', nothing: 'no-effect' });
  assert.equal(result.reason, 'none-eligible');
});

test('page warnings, changed status and untracked dirty fields stop a candidate', () => {
  const result = verifyBranches({ control, candidates: [
    candidate('alert', { after: { alerts: ['Approval missing'] } }),
    candidate('status', { after: { statuses: ['Blocked by policy'] } }),
    candidate('surcharge', { after: { dirty: ['hours', 'surcharge'] } }, { fields: ['hours'] }),
    candidate('threw', { thrown: 'TypeError' }),
    candidate('wrong', {}, { accepts: () => false }),
  ] });
  assert.deepEqual(verdicts(result), { alert: 'page-warned', status: 'status-changed', surcharge: 'unexpected-dirty-field', threw: 'action-threw', wrong: 'wrong-outcome' });
});

test('a warning already on the page and a declared status or field do not block', () => {
  const result = verifyBranches({ control, candidates: [candidate('a', { before: { alerts: ['Old notice'] },
    after: { alerts: ['Old notice'], statuses: ['Ready'], dirty: ['hours'] } }, { fields: ['hours'], statuses: ['Ready'] })] });
  assert.equal(result.decision, 'eligible');
});

test('the browser refusal of the expected write is not an action failure', () => {
  assert.equal(verifyBranches({ control, candidates: [candidate('a', { thrown: 'NotAllowedError' })] }).winner, 'a');
});

test('different eligible effects abstain and identical effects choose the first', () => {
  const other = { attempt: 'form', target: 'https://app.test/items/7/archive' };
  const ambiguous = verifyBranches({ control, candidates: [candidate('a'), { id: 'b', text: branch({ attempts: [[other.attempt, other.target]] }), expect: other }] });
  assert.equal(ambiguous.reason, 'ambiguous-effects');
  assert.equal(verifyBranches({ control, candidates: [candidate('a'), candidate('b')] }).winner, 'a');
});

test('the same field with different values is an ambiguous effect', () => {
  const value = digest => ({ after: { dirty: ['hours'], values: [['hours', digest]] } });
  const result = verifyBranches({ control, candidates: [candidate('eight', value('aaaa'), { fields: ['hours'] }), candidate('eight-hundred', value('bbbb'), { fields: ['hours'] })] });
  assert.equal(result.reason, 'ambiguous-effects');
});

test('an observation that could not hold the whole page is not trusted', () => {
  const result = verifyBranches({ control, candidates: [candidate('a', { after: { truncated: true } })] });
  assert.deepEqual(verdicts(result), { a: 'observation-truncated' });
  assert.equal(verifyBranches({ control: branch({ after: { truncated: true } }), candidates: [candidate('a')] }).reason, 'control-invalid');
});

test('an invalid control or candidate list abstains', () => {
  assert.equal(verifyBranches({ control: branch({ ended: 'deadline' }), candidates: [candidate('a')] }).reason, 'control-invalid');
  assert.equal(verifyBranches({ control: branch({ thrown: 'TypeError' }), candidates: [candidate('a')] }).reason, 'control-invalid');
  assert.equal(verifyBranches({ control, candidates: [] }).reason, 'invalid-candidates');
  assert.equal(verifyBranches({ control, candidates: [candidate('a'), candidate('a')] }).reason, 'invalid-candidates');
});

test('the server check fails closed and is skipped when nothing is eligible', async () => {
  for (const [attest, reason] of [[undefined, 'attestation-required'], [async () => ({ holds: false }), 'prerequisite-not-confirmed'],
    [async () => null, 'prerequisite-not-confirmed'], [async () => { throw new Error('offline'); }, 'attestation-failed']]) {
    const result = await decideBranch({ control, candidates: [candidate('a')], attest });
    assert.equal(result.decision, 'abstain');
    assert.equal(result.reason, reason);
    assert.equal(result.winner, null);
  }
  let reads = 0;
  await decideBranch({ control, candidates: [candidate('a', { attempts: [] })], attest: async () => { reads += 1; return { holds: true }; } });
  assert.equal(reads, 0);
});

test('the branch expression is valid JavaScript and rejects an empty action', () => {
  assert.doesNotThrow(() => new Function(`return ${branchExpression('document.querySelector("form").requestSubmit()')}`));
  assert.throws(() => branchExpression(' '), TypeError);
});

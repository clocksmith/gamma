import test from 'node:test';
import assert from 'node:assert/strict';
import { collectObservedFacts, learnRepairBoundary, checkRepairBoundary } from '../../src/client/repair-boundary.js';

const binding = 'opbind-v1:' + 'a'.repeat(64);
const alternative = 'opbind-v1:' + 'b'.repeat(64);
const response = (json, extra = {}) => ({
  sameOrigin: true, method: 'GET', transport: 'xhr', status: 200, sourceRole: 'record', json, ...extra,
});
const observe = (...args) => collectObservedFacts(args);
const learn = (positive, negative) => learnRepairBoundary({ positive, negative, intendedEffect: binding });

test('catalog retains bounded raw evidence and not arbitrary opaque strings or unsafe data', () => {
  const attested = observe(response({
    id: 19, recordId: 19, refreshToken: 0, access_token: 1, note: 'PT12H', description: 255, opaque: 'test',
    estimatedTime: 'PT8H', lockVersion: 7, policy: { phase: 4 }, details: [{ identifier: 0 }],
    irrelevant: true, status: { href: 'https://local.invalid/status' },
    absentValue: null, unbounded: Infinity,
  }), response({ lockVersion: 11 }, { sameOrigin: false }),
  response({ lockVersion: 22 }, { method: 'POST' }),
  response({ lockVersion: 33 }, { status: 409 }));
  assert.equal(attested.status, 'observed');
  assert.deepEqual({ ...attested.facts }, {
    'record:/estimatedTime': 'PT8H', 'record:/lockVersion': 7,
    'record:/policy/phase': 4, 'record:/irrelevant': true,
  });
  assert.equal(observe(response({ lockVersion: 11 }), response({ lockVersion: 22 })).reason, 'ambiguous-source-role');
  assert.equal(collectObservedFacts(Array(17).fill(response({ x: 1 }))).reason, 'catalog-budget');
});

test('learns unique minimum unary guard, transfers narrowly, and never authorizes a write', () => {
  const yes = observe(response({ lockVersion: 9, stateCode: 2 }));
  const no = observe(response({ lockVersion: 9, stateCode: 3 }));
  const learned = learn([yes], [no]);
  assert.equal(learned.status, 'learned');
  assert.deepEqual(learned.guard, [{ kind: 'equals-literal', left: 'record:/stateCode', value: 2 }]);
  assert.equal(learned.trainingReadCount, 1);
  const seen = checkRepairBoundary(learned, observe(response({ stateCode: 2, lockVersion: 99 })), binding);
  assert.deepEqual(seen, { status: 'eligible-for-review' });
  assert.equal(checkRepairBoundary(learned, observe(response({ stateCode: 3 })), binding).reason, 'guard-mismatch');
  assert.equal(checkRepairBoundary(learned, observe(response({ stateCode: 'bad' })), binding).reason, 'unavailable-runtime-evidence');
  assert.equal(checkRepairBoundary(learned, yes, alternative).reason, 'operation-reference-mismatch');
});

test('different raw values across multiple teaching records can isolate a field relation', () => {
  const example = (a, b) => observe(response({ approvedVersion: a, lockVersion: b }));
  const learned = learn([example(4, 4), example(9, 9)], [example(4, 9)]);
  assert.equal(learned.status, 'learned');
  assert.deepEqual(learned.guard, [
    { kind: 'equals-field', left: 'record:/approvedVersion', right: 'record:/lockVersion' },
  ]);
  assert.equal(learned.trainingReadCount, 2);
  assert.deepEqual(checkRepairBoundary(learned, example(99, 99), binding), { status: 'eligible-for-review' });
  assert.equal(checkRepairBoundary(learned, example(99, 101), binding).reason, 'guard-mismatch');
  assert.equal(checkRepairBoundary(learned, observe(response({ lockVersion: 99 })), binding).reason, 'unavailable-runtime-evidence');
});

test('conjunction separates two negatives only when both fields are read', () => {
  const example = (one, two) => observe(response({ open: one, separate: two }));
  const found = learn([example(1, 2)], [example(1, 3), example(0, 2)]);
  assert.equal(found.status, 'learned');
  assert.equal(found.trainingReadCount, 2);
  assert.deepEqual(found.guard.map(t => t.left), ['record:/open', 'record:/separate']);
  assert.equal(checkRepairBoundary(found, example(1, 3), binding).reason, 'guard-mismatch');
});

test('abstains on indistinguishable, ambiguous, and unavailable evidence', () => {
  const pos = observe(response({ stateCode: 1, second: 8 }));
  assert.equal(learn([pos], [pos]).reason, 'no-separating-guard');
  const neg = observe(response({ stateCode: 2, second: 9 }));
  assert.equal(learn([pos], [neg]).reason, 'ambiguous-minimum');
  assert.equal(learn([pos], [observe(response({}))]).reason, 'no-separating-guard');
  assert.equal(learn([pos], [{ status: 'abstain' }]).reason, 'unavailable-teaching-evidence');
  assert.equal(learnRepairBoundary({ positive:[pos], negative:[neg], intendedEffect:'not-a-binding' }).reason, 'invalid-operation-reference');
});

test('rejects malformed frozen guards and never treats an empty rule as universal', () => {
  const obs = observe(response({ stateCode: 1 }));
  const frozen = terms => ({ status: 'learned', intendedEffect: binding, guard: terms });
  assert.equal(checkRepairBoundary(frozen([]), obs, binding).reason, 'unavailable-runtime-evidence');
  assert.equal(checkRepairBoundary(frozen([{ kind:'sometimes', left:'record:/stateCode' }]), obs, binding).reason, 'unavailable-runtime-evidence');
  assert.equal(checkRepairBoundary(frozen([{ kind:'equals-literal', left:'record:/stateCode', value: true }]), obs, binding).reason, 'unavailable-runtime-evidence');
});

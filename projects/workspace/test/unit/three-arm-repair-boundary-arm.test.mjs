import assert from 'node:assert/strict';
import { test } from 'node:test';
import {
  createTeacher, decide, intendedEffect, observe, openProjectDuration, validateReadPlan,
} from '../../qualification/workflow-generalization/three-arm/repair-boundary-arm.mjs';

const PLAN = [
  { role: 'record', path: '/api/v3/work_packages/{target}' },
  { role: 'approval', follow: { role: 'record', link: 'parent' } },
];
// A stand-in application: each order points at an approval that has hours and a status.
function app(records) {
  const calls = [];
  const get = async path => {
    calls.push(path);
    const id = Number(path.split('/').pop());
    const r = records[id];
    if (!r) return { ok: true, status: 404, body: { message: 'not found' } };
    return { ok: true, status: 200, body: { id, lockVersion: 1, estimatedTime: openProjectDuration(r.hours), subject: 'free text is never a fact',
      _links: { status: { href: `/api/v3/statuses/${r.status}` }, project: { href: '/api/v3/projects/1' },
        ...(r.parent ? { parent: { href: `/api/v3/work_packages/${r.parent}` } } : {}) } } };
  };
  return { calls, get };
}
const APPROVED = 16;
const HOLD = 17;
const records = {
  1: { hours: 24, status: APPROVED }, 2: { hours: 8, status: 15, parent: 1 },      // valid: approval says 24, approved
  3: { hours: 16, status: APPROVED }, 4: { hours: 8, status: 15, parent: 3 },      // invalid for 24: approval says 16
  5: { hours: 24, status: HOLD }, 6: { hours: 8, status: 15, parent: 5 },          // invalid: approval on hold
  7: { hours: 40, status: APPROVED }, 8: { hours: 8, status: 15, parent: 7 },      // valid for 40
  9: { hours: 40, status: HOLD }, 10: { hours: 8, status: 15, parent: 9 },         // unseen, invalid
  11: { hours: 8, status: 15 },                                                    // unseen, no approval at all
  12: { hours: 56, status: APPROVED }, 13: { hours: 8, status: 15, parent: 12 },   // unseen, valid for 56
};
const route = (workPackageId, workHours) => ({ familyId: 'fam', project: 'p', workPackageId, workHours });

test('read plans are checked before use', () => {
  assert.deepEqual(validateReadPlan(PLAN), []);
  assert.ok(validateReadPlan([]).length);
  assert.ok(validateReadPlan([...PLAN, ...PLAN]).length);
  assert.ok(validateReadPlan([{ role: 'intent', path: '/api/v3/x' }]).length);
  assert.ok(validateReadPlan([{ role: 'a', path: '/api/v3/work_packages/{other}' }]).length);
  assert.ok(validateReadPlan([{ role: 'a', path: 'http://example.com/api/v3/x' }]).length);
  assert.ok(validateReadPlan([{ role: 'a', follow: { role: 'missing', link: 'parent' } }]).length);
  assert.ok(validateReadPlan([{ role: 'a', path: '/api/v3/x', follow: { role: 'a', link: 'parent' } }]).length);
});

test('an observation holds the request and projected scalars, never free text or links', async () => {
  const { get, calls } = app(records);
  const { observation, reads, rolesRead } = await observe({ plan: PLAN, route: route(2, 24), get });
  assert.equal(reads, 2);
  assert.deepEqual(rolesRead, ['record', 'approval']);
  assert.deepEqual(calls, ['/api/v3/work_packages/2', '/api/v3/work_packages/1']);
  assert.equal(observation.facts['intent:/estimatedTime'], 'P1D');
  assert.equal(observation.facts['approval:/estimatedTime'], 'P1D');
  assert.equal(observation.facts['approval:/statusCode'], APPROVED);
  assert.ok(Object.keys(observation.facts).every(k => !/subject|href|links/i.test(k)));
});

test('teaching, freezing and deciding: the learned guard transfers to routes it never saw', async () => {
  const { get } = app(records);
  const teacher = createTeacher(['fam']);
  assert.equal((await teacher.addExample('fam', 'valid', route(2, 24), get)).ok, false);
  assert.equal(teacher.setReadPlan('fam', PLAN).ok, true);
  assert.equal((await teacher.addExample('fam', 'valid', route(2, 24), get)).ok, true);
  assert.equal(teacher.learn('fam').status, 'abstain');
  await teacher.addExample('fam', 'invalid', route(4, 24), get);
  await teacher.addExample('fam', 'invalid', route(6, 24), get);
  // One valid example is not enough: the cheapest guard that fits it pins the hours to 24.
  const narrow = teacher.learn('fam');
  assert.equal(narrow.status, 'learned');
  assert.ok(narrow.guard.some(term => term.kind === 'equals-literal' && term.value === 'P1D'));
  await teacher.addExample('fam', 'valid', route(8, 40), get);
  const boundary = teacher.learn('fam');
  assert.equal(boundary.status, 'learned');
  assert.ok(boundary.guard.some(term => term.kind === 'equals-field'));
  assert.equal(boundary.intendedEffect, intendedEffect('fam'));
  const frozen = teacher.freeze();
  assert.match(frozen.sha256, /^[a-f0-9]{64}$/);
  assert.equal(teacher.freeze().sha256, frozen.sha256);
  const artifact = JSON.parse(frozen.text);
  assert.deepEqual(await decide(artifact, route(13, 56), get), { decision: 'write', reason: 'guard holds', reads: 2 });
  assert.equal((await decide(artifact, route(13, 32), get)).decision, 'stop');
  assert.equal((await decide(artifact, route(10, 40), get)).decision, 'stop');
  const orphan = await decide(artifact, route(11, 8), get);
  assert.equal(orphan.decision, 'stop');
  assert.equal(orphan.reason, 'unavailable-runtime-evidence');
  assert.equal((await decide(artifact, { ...route(13, 56), familyId: 'other' }, get)).decision, 'stop');
});

test('a family that was never taught, or cannot be separated, stops on every route', async () => {
  const { get } = app(records);
  const teacher = createTeacher(['fam', 'untaught']);
  teacher.setReadPlan('fam', [{ role: 'record', path: '/api/v3/work_packages/{target}' }]);
  await teacher.addExample('fam', 'valid', route(2, 24), get);
  await teacher.addExample('fam', 'invalid', route(6, 24), get);
  assert.equal(teacher.learn('fam').reason, 'no-separating-guard');
  const artifact = teacher.freeze().artifact;
  assert.equal(artifact.families.untaught.boundary.reason, 'never-learned');
  assert.equal((await decide(artifact, route(2, 24), get)).decision, 'stop');
  assert.equal((await decide(artifact, { ...route(2, 24), familyId: 'untaught' }, get)).decision, 'stop');
});

test('the requested hours are written as the application writes durations', () => {
  // Observed on OpenProject 14.0.0: 8 hours is PT8H, 16 is PT16H, 24 is P1D, 40 is P1DT16H.
  assert.deepEqual([8, 16, 24, 40, 48, 56, 1].map(openProjectDuration), ['PT8H', 'PT16H', 'P1D', 'P1DT16H', 'P2D', 'P2DT8H', 'PT1H']);
});

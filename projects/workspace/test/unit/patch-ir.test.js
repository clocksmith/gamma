import assert from 'node:assert/strict';
import { MAX_PATCHES_V1, PATCH_IR_V1, normalizePatchV1, schedulePatchDependenciesV1 } from '../../src/client/patch-ir.js';

const patch = (id, options = {}) => ({
  version: PATCH_IR_V1, id, mode: 'local', after: [],
  reads: [], writes: [], guards: [], effects: [], verifier: { id: 'local.verify', version: 1 },
  ...options,
});
const read = (id, resource) => patch(id, { reads: [resource], guards: [{ resource, fact: 'ready' }] });
const write = (id, resource) => patch(id, { writes: [resource], effects: [{ resource, fact: 'updated' }] });

const a = read('a', 'doc:x'), z = read('z', 'doc:x');
const independent = { version: PATCH_IR_V1, order: ['a', 'z'], dependencies: [] };
assert.deepEqual(schedulePatchDependenciesV1([z, a]), independent);
assert.deepEqual(schedulePatchDependenciesV1([a, z]), independent);
assert.deepEqual(schedulePatchDependenciesV1([z, write('a', 'doc:y')]), independent);
for (const pair of [[write('z', 'doc:x'), a], [z, write('a', 'doc:x')],
  [write('z', 'doc:x'), write('a', 'doc:x')]]) {
  assert.deepEqual(schedulePatchDependenciesV1(pair), {
    version: PATCH_IR_V1, order: ['z', 'a'], dependencies: [{ before: 'z', after: 'a' }],
  });
}
for (const mode of ['unknown', 'external', 'ambient']) {
  const result = schedulePatchDependenciesV1([z, patch('m', { mode }), a]);
  assert.deepEqual(result.order, ['z', 'm', 'a']);
  assert.deepEqual(result.dependencies, [{ before: 'm', after: 'a' }, { before: 'z', after: 'm' }]);
}
assert.deepEqual(schedulePatchDependenciesV1([patch('c', { after: ['a'] }), z, a]).order, ['a', 'c', 'z']);
assert.throws(() => schedulePatchDependenciesV1([a, a]), /duplicate patch ID/);
assert.throws(() => schedulePatchDependenciesV1([patch('a', { after: ['b'] })]), /Unknown patch dependency/);
assert.throws(() => schedulePatchDependenciesV1([patch('a', { after: ['b'] }), patch('b', { after: ['a'] })]), /Cyclic/);
assert.throws(() => schedulePatchDependenciesV1([
  { ...write('z', 'doc:x'), after: ['a'] }, a,
]), /Cyclic/);
assert.throws(() => normalizePatchV1(patch('a', { after: ['a'] })), /itself/);
assert.throws(() => normalizePatchV1(patch('a', { writes: ['doc:x'] })), /effect for every write/);
assert.throws(() => normalizePatchV1(patch('a', { guards: [{ resource: 'doc:x', fact: 'ready' }] })), /guard resource/);
assert.throws(() => normalizePatchV1(patch('a', { effects: [{ resource: 'doc:x', fact: 'updated' }] })), /effect resource/);
assert.throws(() => normalizePatchV1(patch('a', {
  reads: ['doc:x'], guards: [{ resource: 'doc:x', fact: 'ready' }, { resource: 'doc:x', fact: 'busy' }],
})), /ambiguous patch guard/);
assert.throws(() => normalizePatchV1(patch('a', { verifier: { id: 'unversioned' } })), /verifier identity/);
assert.throws(() => normalizePatchV1(patch('a', { execute: 'arbitrary-command' })), /IR v1 declaration/);
assert.throws(() => normalizePatchV1(patch('a', { reads: Array.from({ length: 33 }, (_, n) => `r${n}`) })), /reads/);
const atBound = Array.from({ length: MAX_PATCHES_V1 }, (_, n) => patch(`p${n}`));
assert.equal(schedulePatchDependenciesV1(atBound).order.length, MAX_PATCHES_V1);
assert.throws(() => schedulePatchDependenciesV1([...atBound, patch('extra')]), /schedule size/);
console.log('ok: typed patch guards/effects/verifier, interference and fences, canonical topological order, no executable fields, bounded contracts');

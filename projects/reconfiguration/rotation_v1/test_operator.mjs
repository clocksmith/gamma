import assert from 'node:assert/strict';
import { freezeRotation, replayRotation } from './operator.mjs';
const identity = Object.fromEntries(['modelArtifactSha256', 'promptSha256', 'captureContractSha256', 'deriveShaderSha256', 'applyShaderSha256'].map(key => [key, 'a'.repeat(64)]));
identity.runtimeCommit = 'b'.repeat(40);
const input = { basis: new Float32Array([1,0,0,0,1,0]), channels: 3, layer: 30, theta: 0.05, epsilon: 1e-6, status: 1, identity };
const record = freezeRotation(input);
const replay = replayRotation(JSON.parse(JSON.stringify(record)));
assert.deepEqual(replay.basis, input.basis);
assert.equal(replay.record.operatorSha256, record.operatorSha256);
input.basis[0] = 9;
assert.equal(replayRotation(record).basis[0], 1);
for (const change of [{ theta: -record.theta }, { layer: 31 }, { basis: record.basis.slice(4) }, { extra: true }, { identity: { ...identity, runtimeCommit: 'c'.repeat(40) } }]) {
  assert.throws(() => replayRotation({ ...record, ...change }));
}
assert.throws(() => freezeRotation(input), /orthonormal/);
assert.throws(() => freezeRotation({ ...input, theta: Infinity }), /parameters/);
assert.throws(() => freezeRotation({ ...input, status: -1 }), /parameters/);
const degenerate = freezeRotation({ ...input, basis: new Float32Array(6), status: 0 });
assert.deepEqual(replayRotation(degenerate).basis, new Float32Array(6));
console.log('rotation operator exact-byte replay, independent ownership, corruption and provenance checks passed');

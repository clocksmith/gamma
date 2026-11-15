import { createHash } from 'node:crypto';

const sha256 = bytes => createHash('sha256').update(bytes).digest('hex');
const identityFields = ['modelArtifactSha256', 'promptSha256', 'captureContractSha256', 'deriveShaderSha256', 'applyShaderSha256'];
function validateIdentity(identity) {
  if (!identity || identityFields.some(key => !/^[0-9a-f]{64}$/.test(identity[key]))
      || !/^[0-9a-f]{40}$/.test(identity.runtimeCommit)) throw new Error('Complete pinned source and workload identities are required.');
}
function validatePlane(basis, channels, status) {
  if (!(basis instanceof Float32Array) || basis.length !== channels * 2 || !basis.every(Number.isFinite)) throw new Error('Expected complete finite f32 basis.');
  if (status === 0) {
    if (basis.some(x => x !== 0)) throw new Error('Degenerate identity requires zero basis.');
    return;
  }
  let a = 0, b = 0, dot = 0;
  for (let i = 0; i < channels; i++) {
    a += basis[i] ** 2; b += basis[channels + i] ** 2; dot += basis[i] * basis[channels + i];
  }
  if (Math.abs(a - 1) > 2e-5 || Math.abs(b - 1) > 2e-5 || Math.abs(dot) > 2e-5) throw new Error('Basis is not orthonormal within the v1 f32 tolerance.');
}
function encodePlane(basis) {
  const bytes = Buffer.alloc(basis.byteLength);
  basis.forEach((value, i) => bytes.writeFloatLE(value, i * 4));
  return bytes;
}
export function freezeRotation({ basis, channels, layer, theta, epsilon, status, identity }) {
  if (!Number.isSafeInteger(channels) || channels < 1 || !Number.isSafeInteger(layer) || layer < 0
      || !Number.isFinite(theta) || !Number.isFinite(Math.fround(theta))
      || !Number.isFinite(epsilon) || !Number.isFinite(Math.fround(epsilon)) || Math.fround(epsilon) <= 0
      || (status !== 0 && status !== 1)) throw new Error('Invalid explicit rotation parameters.');
  validateIdentity(identity); validatePlane(basis, channels, status);
  const bytes = encodePlane(basis);
  const payload = {
    schema: 'gamma.request-channel-rotation/v1',
    rule: 'signed-instruction-complement-mean-orthonormal-plane/v1',
    channels, layer, theta: Math.fround(theta), epsilon: Math.fround(epsilon), status,
    basisEncoding: 'f32-little-endian-base64', basis: bytes.toString('base64'), basisSha256: sha256(bytes),
    identity: Object.fromEntries([...identityFields, 'runtimeCommit'].map(key => [key, identity[key]])),
  };
  return Object.freeze({ ...payload, operatorSha256: sha256(JSON.stringify(payload)), identity: Object.freeze(payload.identity) });
}
export function replayRotation(record) {
  if (!record || record.schema !== 'gamma.request-channel-rotation/v1'
      || record.rule !== 'signed-instruction-complement-mean-orthonormal-plane/v1'
      || record.basisEncoding !== 'f32-little-endian-base64' || typeof record.basis !== 'string') throw new Error('Unsupported rotation record.');
  const bytes = Buffer.from(record.basis, 'base64');
  if (bytes.toString('base64') !== record.basis || bytes.length !== record.channels * 8) throw new Error('Noncanonical or incomplete basis encoding.');
  const basis = new Float32Array(bytes.length / 4);
  basis.forEach((_, i) => { basis[i] = bytes.readFloatLE(i * 4); });
  const checked = freezeRotation({ ...record, basis });
  if (checked.operatorSha256 !== record.operatorSha256 || checked.basisSha256 !== record.basisSha256) throw new Error('Rotation identity mismatch.');
  if (Object.keys(record).sort().join() !== Object.keys(checked).sort().join()) throw new Error('Unknown rotation record fields.');
  return { record: checked, basis };
}

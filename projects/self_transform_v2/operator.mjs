import { createHash } from 'node:crypto';

export const RULE = 'scalar-probe-tanh-v2';
export function vector(value, length = value?.length) {
  if (!Array.isArray(value) || value.length !== length || !value.length
      || !value.every(Number.isFinite)) throw new Error('Invalid finite vector');
  return value;
}

// No closure state, history, target identity, evaluator, or random source.
// The very same interface accepts task weights or the operator's own weights.
export function estimate(theta, experience) {
  vector(theta);
  const { directions, plus, minus, radius } = experience;
  if (!Number.isFinite(radius) || radius <= 0 || !Array.isArray(directions)
      || directions.length !== 4) throw new Error('Invalid probes');
  vector(plus, 4); vector(minus, 4);
  directions.forEach(d => vector(d, theta.length));
  return theta.map((_, i) => directions.reduce((sum, d, j) =>
    sum + (plus[j] - minus[j]) * d[i] / (2 * radius), 0) / 4);
}

export function transform(phi, theta, experience) {
  vector(phi, 4);
  const gradient = estimate(theta, experience);
  const scale = 0.1 * (1 + Math.tanh(phi[3]));
  return vector(theta.map((w, i) => w + scale * Math.tanh(
    phi[0] * gradient[i] + phi[1] * w + phi[2],
  )));
}

export function digest(value) {
  return createHash('sha256').update(JSON.stringify(value)).digest('hex');
}

export function serialize(phi) {
  vector(phi, 4);
  const bytes = Buffer.alloc(32);
  phi.forEach((value, i) => bytes.writeDoubleLE(value, i * 8));
  const payload = { schema: 'gamma.self-transform/v2', rule: RULE, weightsHex: bytes.toString('hex') };
  return JSON.stringify({ ...payload, sha256: digest(payload) });
}

export function reconstruct(text) {
  const data = JSON.parse(text);
  if (Object.keys(data).sort().join() !== 'rule,schema,sha256,weightsHex'
      || data.schema !== 'gamma.self-transform/v2' || data.rule !== RULE) {
    throw new Error('Unsupported artifact');
  }
  if (typeof data.weightsHex !== 'string' || !/^[0-9a-f]{64}$/.test(data.weightsHex)) {
    throw new Error('Invalid weight bytes');
  }
  const bytes = Buffer.from(data.weightsHex, 'hex');
  const weights = Array.from({ length: 4 }, (_, i) => bytes.readDoubleLE(i * 8));
  vector(weights, 4);
  const payload = { schema: data.schema, rule: data.rule, weightsHex: data.weightsHex };
  if (digest(payload) !== data.sha256) throw new Error('Corrupt artifact');
  return weights;
}

export function random(seed) {
  let state = seed >>> 0;
  return () => {
    state = (Math.imul(1664525, state) + 1013904223) >>> 0;
    return state / 4294967296;
  };
}

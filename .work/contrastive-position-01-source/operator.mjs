import assert from 'node:assert/strict';

// Evidence consists only of the model's own full/ablated-prompt representations.
export function derive(activation, hidden, reference, alpha = 0.25, epsilon = 1e-9) {
  assert.ok(activation.length > 0 && hidden.length > 0 && hidden.length === reference.length);
  assert.ok([alpha, epsilon].every(Number.isFinite) && Math.abs(alpha) <= 1 && epsilon > 0);
  assert.ok([activation, hidden, reference].every(v => Array.from(v).every(Number.isFinite)));
  const norm = activation.reduce((s, x) => s + x*x, 0);
  const hiddenNorm = Math.hypot(...hidden);
  const difference = Float32Array.from(hidden, (x, i) => x - reference[i]);
  const differenceNorm = Math.hypot(...difference);
  const bound = Math.min(1, hiddenNorm / (differenceNorm + epsilon));
  const a = Float32Array.from(activation, x => x / (norm + epsilon));
  const b = Float32Array.from(difference, x => alpha * bound * x);
  assert.ok([a,b].every(v => Array.from(v).every(Number.isFinite)));
  return { a, b, activationSquaredNorm: norm, hiddenNorm, differenceNorm, bound };
}

export function correction(operator, activation) {
  assert.equal(operator.a.length, activation.length);
  const dot = operator.a.reduce((s, x, i) => s + x * activation[i], 0);
  return Float32Array.from(operator.b, x => x * dot);
}

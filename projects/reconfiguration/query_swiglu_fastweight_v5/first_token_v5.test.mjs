import test from 'node:test';
import assert from 'node:assert/strict';
import { firstSupportToken } from './first_token_v5.mjs';

test('keeps an allowed winner; replaces an off-code winner with the best supported start', () => {
  const logits = Float32Array.of(-3, 9, 4, 7);
  assert.deepEqual(firstSupportToken(logits, 1, [2, 3]), { raw: 1, best_allowed: 3, logit_gap: 2 });
  assert.deepEqual(firstSupportToken(logits, 1, [3, 1]), { raw: 1, best_allowed: 1, logit_gap: 0 });
});

test('ties follow vocabulary order independently of the order of the support lines', () => {
  assert.equal(firstSupportToken([8, 7, 7], 0, [2, 1]).best_allowed, 1);
  assert.throws(() => firstSupportToken([0], 0, []));
  assert.throws(() => firstSupportToken([0], 0, [7]));
});

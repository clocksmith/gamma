import test from 'node:test';
import assert from 'node:assert/strict';
import { scaleCompiledStopChannel } from './stop_channel_control.mjs';
const make = () => ({
  rank: 4, dHidden: 2, uniqTargetTokens: [11, 22],
  layers: new Map([[23, {
    rank: 4, scale: 1, alpha: 1,
    a: new Float32Array([1, 2, 3, 4]),
    b: new Float32Array([1, 2, 3, 4, 5, 6, 7, 8]),
  }]]),
});
test('identity gain exactly preserves coefficients and metadata', () => {
  const lora = make(), out = scaleCompiledStopChannel(lora);
  assert.deepEqual(out, lora);
  assert.notEqual(out.layers, lora.layers);
  assert.notEqual(out.layers.get(23).b, lora.layers.get(23).b);
});
test('zero gain removes only stop channel, without mutating original', () => {
  const lora = make(), out = scaleCompiledStopChannel(lora, 0);
  assert.deepEqual([...out.layers.get(23).b], [1,2,3,4,5,6,0,0]);
  assert.deepEqual([...lora.layers.get(23).b], [1,2,3,4,5,6,7,8]);
  assert.deepEqual(out.layers.get(23).a, lora.layers.get(23).a);
});
test('half gain halves only isolated stop contribution', () => {
  const lora = make(), out = scaleCompiledStopChannel(lora, 0.5);
  assert.deepEqual([...out.layers.get(23).b], [1,2,3,4,5,6,3.5,4]);
});
test('reject invalid gains and unknown adapter layout', () => {
  for (const value of [-1, 2, NaN, Infinity]) {
    assert.throws(() => scaleCompiledStopChannel(make(), value));
  }
  const lora = make(); lora.rank = 9;
  assert.throws(() => scaleCompiledStopChannel(lora));
});

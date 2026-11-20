import assert from 'node:assert/strict';
import { assertGpuReport } from '../support/gpu-composition-oracle.js';

const report = { queueCompleted: true, adapter: { isFallbackAdapter: false }, values: [2, 4, 6, 8, 10, 12, 14, 16],
  pixels: Array.from({ length: 64 }, () => [0, 255, 0, 255]).flat(), canvasFrames: 2, format: 'bgra8unorm' };
assertGpuReport(report);
for (const change of [
  value => { value.values[7] = 0; },
  value => { value.values.push(18); },
  value => { value.pixels[255] = 0; },
  value => { value.pixels.pop(); },
  value => { value.adapter.isFallbackAdapter = true; },
  value => { delete value.adapter.isFallbackAdapter; },
  value => { value.error = 'GPU error'; },
  value => { value.queueCompleted = false; },
  value => { value.canvasFrames = 0; },
  value => { value.format = 'unexpected'; },
]) {
  const bad = structuredClone(report);
  change(bad);
  assert.throws(() => assertGpuReport(bad));
}
console.log('ok: GPU composition rejects wrong final values/pixels, incomplete output and software/unknown adapters');

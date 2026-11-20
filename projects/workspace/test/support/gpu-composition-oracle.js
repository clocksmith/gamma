// Host-owned exact oracle: neither page success text nor dispatch counters admit output.
import assert from 'node:assert/strict';

function assertGpuReport(report) {
  assert.equal(report.error, undefined);
  assert.equal(report.queueCompleted, true, 'queue completion must be established');
  assert.equal(report.adapter.isFallbackAdapter, false, 'a physical adapter must be established');
  assert.deepEqual(report.values, [2, 4, 6, 8, 10, 12, 14, 16]);
  assert.deepEqual(report.pixels, Array.from({ length: 64 }, () => [0, 255, 0, 255]).flat());
  assert.equal(report.canvasFrames, 2);
  assert.ok(['rgba8unorm', 'bgra8unorm'].includes(report.format));
}

export { assertGpuReport };

'use strict';

// 936. Stamping The Sequence: reverse erasure with mismatch dependency queues.
// O(n * m) time and space, n = target length, m = stamp length. Inputs are preserved.
function solve(stamp, target) {
  const width = stamp.length;
  const length = target.length;
  if (width > length) return [];
  const pending = new Int32Array(length - width + 1);
  const waiting = Array.from({ length }, () => []);
  const ready = [];
  for (let start = 0; start < pending.length; start += 1) {
    for (let offset = 0; offset < width; offset += 1) {
      if (target[start + offset] !== stamp[offset]) {
        pending[start] += 1;
        waiting[start + offset].push(start);
      }
    }
    if (pending[start] === 0) ready.push(start);
  }
  const erased = new Uint8Array(length);
  let removed = 0;
  const answer = [];
  for (let head = 0; head < ready.length; head += 1) {
    const start = ready[head];
    answer.push(start);
    for (let index = start; index < start + width; index += 1) {
      if (erased[index]) continue;
      erased[index] = 1;
      removed += 1;
      for (const window of waiting[index]) {
        pending[window] -= 1;
        if (pending[window] === 0) ready.push(window);
      }
    }
  }
  return removed === length ? answer.reverse() : [];
}

const movesToStamp = solve;
class Solution {
  movesToStamp(stamp, target) { return solve(stamp, target); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, movesToStamp };

"use strict";
// Hack2Hire 688fb256b3f942cc1004c00e (Reduce The Maximum To Even K Times) over an INFERRED spec; qualification unknown.

function siftDown(h, i) {
  const n = h.length, v = h[i];
  for (;;) {
    let c = 2 * i + 1;
    if (c >= n) break;
    if (c + 1 < n && h[c + 1] > h[c]) c++;
    if (h[c] <= v) break;
    h[i] = h[c]; i = c;
  }
  h[i] = v;
}

function solve(nums, k, m) {
  const heap = nums.slice(); // binary max-heap on a copy
  for (let i = (heap.length >> 1) - 1; i >= 0; i--) siftDown(heap, i);
  for (let op = 0; op < k; op++) {
    const top = heap[0];
    if (top === 0) break; // every value is 0; later operations change nothing
    heap[0] = (top - (top % 2)) / 2;
    siftDown(heap, 0);
  }
  let total = 0;
  for (const v of heap) total += v; // at most 1e14, exact in a double
  return total % m;
}

function reduceMaximum(nums, k, m) { return solve(nums, k, m); }

module.exports = solve;
module.exports.reduceMaximum = reduceMaximum;

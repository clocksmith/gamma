"use strict";
// Hack2Hire 676efc4fb2c9d428b406a287 (Maximum Combination Health) over an INFERRED spec; qualification unknown.

function solve(health, series, k) {
  const totals = new Map();
  for (let i = 0; i < health.length; i++) totals.set(series[i], (totals.get(series[i]) || 0) + health[i]);
  const heap = [];  // min-heap of at most k totals
  function down(i) {
    for (;;) {
      const l = 2 * i + 1, r = l + 1;
      let m = i;
      if (l < heap.length && heap[l] < heap[m]) m = l;
      if (r < heap.length && heap[r] < heap[m]) m = r;
      if (m === i) return;
      const t = heap[i]; heap[i] = heap[m]; heap[m] = t; i = m;
    }
  }
  for (const total of totals.values()) {
    if (heap.length < k) {
      heap.push(total);
      let i = heap.length - 1;
      while (i > 0 && heap[i] < heap[(i - 1) >> 1]) { const p = (i - 1) >> 1; const t = heap[i]; heap[i] = heap[p]; heap[p] = t; i = p; }
    } else if (total > heap[0]) { heap[0] = total; down(0); }
  }
  let sum = 0;
  for (const v of heap) sum += v;
  return sum;
}

function maxCombinationHealth(health, series, k) { return solve(health, series, k); }

module.exports = solve;
module.exports.maxCombinationHealth = maxCombinationHealth;

"use strict";
// Hack2Hire 6a4813cd3588ba8acc69302a (Top K Largest Elements) over an INFERRED spec; qualification unknown.

function solve(nums, k) {
  if (k === 0) return [];
  const heap = [];
  const down = (i) => {
    const n = heap.length;
    for (;;) {
      const l = 2 * i + 1, r = l + 1;
      let small = i;
      if (l < n && heap[l] < heap[small]) small = l;
      if (r < n && heap[r] < heap[small]) small = r;
      if (small === i) return;
      const t = heap[i]; heap[i] = heap[small]; heap[small] = t;
      i = small;
    }
  };
  for (const value of nums) {
    if (heap.length < k) {
      heap.push(value);
      let i = heap.length - 1;
      while (i > 0) {
        const p = (i - 1) >> 1;
        if (heap[p] <= heap[i]) break;
        const t = heap[i]; heap[i] = heap[p]; heap[p] = t;
        i = p;
      }
    } else if (value > heap[0]) {
      heap[0] = value;
      down(0);
    }
  }
  heap.sort((a, b) => b - a);
  return heap;
}

function kLargest(nums, k) { return solve(nums, k); }

module.exports = solve;
module.exports.kLargest = kLargest;

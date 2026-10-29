"use strict";
// Hack2Hire 6a04f7473141bbc31efdd6f1 (Kth Greatest in Growing Prefix) over an INFERRED spec; qualification unknown.

function siftDown(heap, i) {
  const n = heap.length;
  for (;;) {
    const l = 2 * i + 1, r = l + 1;
    let s = i;
    if (l < n && heap[l] < heap[s]) s = l;
    if (r < n && heap[r] < heap[s]) s = r;
    if (s === i) return;
    const t = heap[i]; heap[i] = heap[s]; heap[s] = t; i = s;
  }
}

function siftUp(heap, i) {
  while (i > 0) {
    const p = (i - 1) >> 1;
    if (heap[p] <= heap[i]) return;
    const t = heap[i]; heap[i] = heap[p]; heap[p] = t; i = p;
  }
}

function solve(arr, k) {
  const heap = [], out = [];
  for (let i = 0; i < arr.length; i++) {
    const value = arr[i];
    if (heap.length < k) { heap.push(value); siftUp(heap, heap.length - 1); }
    else if (value > heap[0]) { heap[0] = value; siftDown(heap, 0); }
    if (i + 1 >= k) out.push(heap[0]);
  }
  return out;
}

function kthGreatestInPrefixes(arr, k) { return solve(arr, k); }

module.exports = solve;
module.exports.kthGreatestInPrefixes = kthGreatestInPrefixes;

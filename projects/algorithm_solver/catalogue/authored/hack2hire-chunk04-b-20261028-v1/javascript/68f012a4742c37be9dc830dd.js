"use strict";
// Hack2Hire 68f012a4742c37be9dc830dd (Build Binary Tree From Character Counts) over an INFERRED spec; qualification unknown.

function less(x, y) { return x[0] < y[0] || (x[0] === y[0] && x[1] < y[1]); }

function heapPush(heap, item) {
  heap.push(item);
  let i = heap.length - 1;
  while (i > 0) {
    const p = (i - 1) >> 1;
    if (!less(heap[i], heap[p])) break;
    [heap[i], heap[p]] = [heap[p], heap[i]];
    i = p;
  }
}

function heapPop(heap) {
  const top = heap[0], last = heap.pop();
  if (heap.length) {
    heap[0] = last;
    let i = 0;
    for (;;) {
      const l = 2 * i + 1, r = l + 1;
      let m = i;
      if (l < heap.length && less(heap[l], heap[m])) m = l;
      if (r < heap.length && less(heap[r], heap[m])) m = r;
      if (m === i) break;
      [heap[i], heap[m]] = [heap[m], heap[i]];
      i = m;
    }
  }
  return top;
}

function solve(s) {
  if (s.length === 0) return null;
  const counts = new Map();
  for (const ch of s) counts.set(ch, (counts.get(ch) || 0) + 1);
  const chars = [...counts.keys()].sort();
  const heap = [];
  let nextId = 0;
  for (const ch of chars) {
    heapPush(heap, [counts.get(ch), nextId, {ch, count: counts.get(ch), left: null, right: null}]);
    nextId++;
  }
  while (heap.length > 1) {
    const a = heapPop(heap), b = heapPop(heap);
    const total = a[0] + b[0];
    heapPush(heap, [total, nextId, {ch: "#", count: total, left: a[2], right: b[2]}]);
    nextId++;
  }
  return heap[0][2];
}

function buildTree(s) { return solve(s); }

module.exports = solve;
module.exports.buildTree = buildTree;

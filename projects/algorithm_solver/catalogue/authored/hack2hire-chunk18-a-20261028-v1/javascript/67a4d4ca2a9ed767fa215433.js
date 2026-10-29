"use strict";
// Hack2Hire 67a4d4ca2a9ed767fa215433 (Maximize Negative Signs) over an INFERRED spec; qualification unknown.

// Binary max-heap over a plain array.
function push(heap, value) {
  heap.push(value);
  let i = heap.length - 1;
  while (i > 0) {
    const parent = (i - 1) >> 1;
    if (heap[parent] >= heap[i]) break;
    [heap[parent], heap[i]] = [heap[i], heap[parent]];
    i = parent;
  }
}

function pop(heap) {
  const top = heap[0];
  const last = heap.pop();
  if (heap.length > 0) {
    heap[0] = last;
    let i = 0;
    for (;;) {
      const l = 2 * i + 1, r = l + 1;
      let s = i;
      if (l < heap.length && heap[l] > heap[s]) s = l;
      if (r < heap.length && heap[r] > heap[s]) s = r;
      if (s === i) break;
      [heap[s], heap[i]] = [heap[i], heap[s]];
      i = s;
    }
  }
  return top;
}

function solve(a) {
  let total = 0;
  const negated = [];
  for (const value of a) {
    total -= value;
    push(negated, value);
    while (total <= 0) total += 2 * pop(negated);
  }
  return negated.length;
}

function maximizeNegativeSigns(a) { return solve(a); }

module.exports = solve;
module.exports.maximizeNegativeSigns = maximizeNegativeSigns;

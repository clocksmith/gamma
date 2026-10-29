"use strict";
// Hack2Hire 6a038c052608e589a944ac93 (Highest Earning Experience Tracker) over an INFERRED spec; qualification unknown.

function before(a, b) {
  // heap order: larger total first, then smaller name
  if (a[0] !== b[0]) return a[0] > b[0];
  return a[1] < b[1];
}

function push(heap, item) {
  heap.push(item);
  let i = heap.length - 1;
  while (i > 0) {
    const p = (i - 1) >> 1;
    if (!before(heap[i], heap[p])) break;
    const t = heap[i]; heap[i] = heap[p]; heap[p] = t;
    i = p;
  }
}

function pop(heap) {
  const last = heap.pop();
  if (heap.length === 0) return;
  heap[0] = last;
  let i = 0;
  for (;;) {
    const l = 2 * i + 1, r = l + 1;
    let m = i;
    if (l < heap.length && before(heap[l], heap[m])) m = l;
    if (r < heap.length && before(heap[r], heap[m])) m = r;
    if (m === i) break;
    const t = heap[i]; heap[i] = heap[m]; heap[m] = t;
    i = m;
  }
}

function solve(operations, experiences, deltas) {
  const totals = new Map();
  const heap = [];
  const out = [];
  for (let i = 0; i < operations.length; i++) {
    if (operations[i] === 'U') {
      const name = experiences[i];
      const total = (totals.has(name) ? totals.get(name) : 0) + deltas[i];
      totals.set(name, total);
      push(heap, [total, name]);
    } else {
      while (heap.length && totals.get(heap[0][1]) !== heap[0][0]) pop(heap);
      out.push(heap.length ? heap[0][1] : '');
    }
  }
  return out;
}

function highestEarningExperiences(operations, experiences, deltas) { return solve(operations, experiences, deltas); }

module.exports = solve;
module.exports.highestEarningExperiences = highestEarningExperiences;

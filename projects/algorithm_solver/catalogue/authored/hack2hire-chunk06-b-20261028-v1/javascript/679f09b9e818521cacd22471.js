"use strict";
// Hack2Hire 679f09b9e818521cacd22471 (Job Scheduler) over an INFERRED spec; qualification unknown.

// Binary min-heap of non-negative numbers.
function push(heap, value) {
  let i = heap.length;
  heap.push(value);
  while (i > 0) {
    const p = (i - 1) >> 1;
    if (heap[p] <= value) break;
    heap[i] = heap[p]; i = p;
  }
  heap[i] = value;
}

function pop(heap) {
  const top = heap[0], last = heap.pop(), n = heap.length;
  if (n) {
    let i = 0;
    for (;;) {
      let c = 2 * i + 1;
      if (c >= n) break;
      if (c + 1 < n && heap[c + 1] < heap[c]) c++;
      if (heap[c] >= last) break;
      heap[i] = heap[c]; i = c;
    }
    heap[i] = last;
  }
  return top;
}

const SHIFT = 262144; // machine numbers stay below 2^18; busy keys pack (end, machine) exactly below 2^53

function solve(jobs) {
  const busy = [], free = [], out = [];
  let machines = 0;
  for (const [jobId, hhmm, duration] of jobs) {
    const start = Number(hhmm.slice(0, 2)) * 60 + Number(hhmm.slice(2));
    while (busy.length && Math.floor(busy[0] / SHIFT) <= start) push(free, pop(busy) % SHIFT);
    const machine = free.length ? pop(free) : ++machines;
    push(busy, (start + Number(duration)) * SHIFT + machine);
    out.push([jobId, "M" + machine]);
  }
  return out;
}

function assignMachines(jobs) { return solve(jobs); }

module.exports = solve;
module.exports.assignMachines = assignMachines;

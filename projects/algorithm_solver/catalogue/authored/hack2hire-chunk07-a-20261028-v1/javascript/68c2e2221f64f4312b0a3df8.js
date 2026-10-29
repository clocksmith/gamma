"use strict";
// Hack2Hire 68c2e2221f64f4312b0a3df8 (Maximum Task Rewards) over an INFERRED spec; qualification unknown.

function solve(tasks) {
  const jobs = tasks.map((t) => [Number(t[1]), Number(t[2])]).sort((a, b) => a[0] - b[0] || a[1] - b[1]);
  const heap = [];
  function pop() {
    const last = heap.pop();
    if (!heap.length) return;
    heap[0] = last;
    let i = 0;
    for (;;) {
      const l = 2 * i + 1, r = l + 1;
      let m = i;
      if (l < heap.length && heap[l] < heap[m]) m = l;
      if (r < heap.length && heap[r] < heap[m]) m = r;
      if (m === i) return;
      const t = heap[i]; heap[i] = heap[m]; heap[m] = t; i = m;
    }
  }
  for (const [deadline, profit] of jobs) {
    heap.push(profit);
    let i = heap.length - 1;
    while (i > 0 && heap[i] < heap[(i - 1) >> 1]) { const p = (i - 1) >> 1; const t = heap[i]; heap[i] = heap[p]; heap[p] = t; i = p; }
    if (heap.length > deadline) pop();
  }
  let sum = 0;
  for (const v of heap) sum += v;
  return sum;
}

function maxTaskRewards(tasks) { return solve(tasks); }

module.exports = solve;
module.exports.maxTaskRewards = maxTaskRewards;

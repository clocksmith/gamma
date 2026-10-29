"use strict";
// Hack2Hire 67735a0732f9cd104fc349d4 (Maximize Task Scheduling Within Time Limit) over an INFERRED spec; qualification unknown.

function solve(n, m, tasks) {
  const size = Math.min(n * m, tasks.length);
  const slots = new Array(size).fill(0);
  const sorted = tasks.slice().sort((x, y) => x - y);
  let started = 0;
  for (const duration of sorted) {
    const free = slots[0];
    if (free + duration > 60) break;
    // replace the root and sift down
    slots[0] = free + duration;
    let i = 0;
    for (;;) {
      const l = 2 * i + 1, r = l + 1;
      let s = i;
      if (l < size && slots[l] < slots[s]) s = l;
      if (r < size && slots[r] < slots[s]) s = r;
      if (s === i) break;
      const t = slots[s];
      slots[s] = slots[i];
      slots[i] = t;
      i = s;
    }
    started++;
  }
  return started;
}

function maxTasksWithinLimit(n, m, tasks) { return solve(n, m, tasks); }

module.exports = solve;
module.exports.maxTasksWithinLimit = maxTasksWithinLimit;

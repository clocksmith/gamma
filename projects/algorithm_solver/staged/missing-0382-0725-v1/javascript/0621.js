'use strict';

// 621. Task Scheduler.

function solve(tasks, n) {
  if (tasks.length === 0) return 0;
  const counts = new Map();
  for (const task of tasks) counts.set(task, (counts.get(task) || 0) + 1);
  let maximum = 0, tied = 0;
  for (const count of counts.values()) maximum = Math.max(maximum, count);
  for (const count of counts.values()) if (count === maximum) tied += 1;
  return Math.max(tasks.length, (maximum - 1) * (n + 1) + tied);
}

const leastInterval = solve;
class Solution {
  leastInterval(tasks, n) { return solve(tasks, n); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, leastInterval };

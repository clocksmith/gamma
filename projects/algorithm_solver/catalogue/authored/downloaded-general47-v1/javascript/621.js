'use strict';

// 621. Task Scheduler (Medium).
// Specification: https://leetcode.com/problems/task-scheduler/description/
function solve(tasks, n) {
  const counts = new Map();
  for (const task of tasks) counts.set(task, (counts.get(task) || 0) + 1);
  let maxCount = 0; let numMax = 0;
  for (const count of counts.values()) {
    if (count > maxCount) { maxCount = count; numMax = 1; }
    else if (count === maxCount) numMax++;
  }
  return Math.max(tasks.length, (maxCount - 1) * (n + 1) + numMax);
}
const leastInterval = solve;
class Solution { leastInterval(tasks, n) { return solve(tasks, n); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, leastInterval };

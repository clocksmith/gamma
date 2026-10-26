'use strict';

// 2365. Task Scheduler II: jump directly to each task type's next legal execution day.
// O(n) expected time and O(n) auxiliary space; inputs are read-only.
function solve(tasks, space) {
  const nextDay = new Map();
  let day = 0;
  for (const task of tasks) {
    day = Math.max(day + 1, nextDay.get(task) || 1);
    nextDay.set(task, day + space + 1);
  }
  return day;
}

const taskSchedulerII = solve;
class Solution {
  taskSchedulerII(tasks, space) { return solve(tasks, space); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, taskSchedulerII };

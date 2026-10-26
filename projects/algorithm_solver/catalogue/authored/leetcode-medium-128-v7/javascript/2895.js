'use strict';

// 2895. Minimum Processing Time: assign descending groups of four tasks to processors in increasing startup order.
// O(n log n) time and O(n) auxiliary space; inputs are read-only.
function solve(processorTime, tasks) {
  const processors = processorTime.slice().sort((left, right) => left - right);
  const ordered = tasks.slice().sort((left, right) => right - left);
  let finish = 0;
  for (let index = 0; index < processors.length; index += 1) {
    finish = Math.max(finish, processors[index] + ordered[4 * index]);
  }
  return finish;
}

const minProcessingTime = solve;
class Solution {
  minProcessingTime(processorTime, tasks) { return solve(processorTime, tasks); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minProcessingTime };

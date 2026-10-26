'use strict';

// 3683. Earliest Time to Finish One Task (Easy).
// Specification: https://leetcode.com/problems/earliest-time-to-finish-one-task/description/
// O(n) time, O(1) auxiliary space; preserve tasks and its rows.
function solve(tasks) {
  let earliest = Infinity;
  for (const [start, duration] of tasks) earliest = Math.min(earliest, start + duration);
  return earliest;
}

const earliestTime = solve;
class Solution {
  earliestTime(tasks) { return solve(tasks); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, earliestTime };

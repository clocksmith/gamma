'use strict';

// 2432. The Employee That Worked on the Longest Task (Easy).
// Specification: https://leetcode.com/problems/the-employee-that-worked-on-the-longest-task/description/
// O(logs.length) time, O(1) space. Break duration ties by the smallest ID.
function solve(n, logs) {
  let previousEnd = 0;
  let longestDuration = -1;
  let bestEmployee = n;
  for (const [employee, end] of logs) {
    const duration = end - previousEnd;
    if (duration > longestDuration ||
        (duration === longestDuration && employee < bestEmployee)) {
      longestDuration = duration;
      bestEmployee = employee;
    }
    previousEnd = end;
  }
  return bestEmployee;
}

const hardestWorker = solve;
class Solution {
  hardestWorker(n, logs) { return solve(n, logs); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, hardestWorker };

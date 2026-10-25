'use strict';

// 1953. Maximum Number of Weeks for Which You Can Work: separate the largest project with milestones from the others.
// O(n) time and O(1) auxiliary space; inputs are read-only.
function solve(milestones) {
  let total = 0;
  let largest = 0;
  for (const count of milestones) {
    total += count;
    largest = Math.max(largest, count);
  }
  const other = total - largest;
  return Math.min(total, 2 * other + 1);
}

const numberOfWeeks = solve;
class Solution {
  numberOfWeeks(milestones) { return solve(milestones); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, numberOfWeeks };

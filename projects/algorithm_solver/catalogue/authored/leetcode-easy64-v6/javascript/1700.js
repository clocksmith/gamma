'use strict';

// 1700. Number of Students Unable to Eat Lunch (Easy).
// Specification: https://leetcode.com/problems/number-of-students-unable-to-eat-lunch/description/
// O(n) time, O(1) space; count preferences instead of rotating the queue; preserve inputs.
function solve(students, sandwiches) {
  const remainingByType = [0, 0];
  for (const preference of students) remainingByType[preference]++;
  let remaining = students.length;
  for (const sandwich of sandwiches) {
    if (remainingByType[sandwich] === 0) break;
    remainingByType[sandwich]--;
    remaining--;
  }
  return remaining;
}

const countStudents = solve;
class Solution {
  countStudents(students, sandwiches) { return solve(students, sandwiches); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countStudents };

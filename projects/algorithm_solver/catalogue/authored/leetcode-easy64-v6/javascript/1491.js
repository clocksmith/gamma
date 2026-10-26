'use strict';

// 1491. Average Salary Excluding the Minimum and Maximum Salary (Easy).
// Specification: https://leetcode.com/problems/average-salary-excluding-the-minimum-and-maximum-salary/description/
// O(n) time, O(1) space; preserve salary; the final division is floating point.
function solve(salary) {
  let total = 0;
  let lowest = salary[0];
  let highest = salary[0];
  for (const value of salary) {
    total += value;
    lowest = Math.min(lowest, value);
    highest = Math.max(highest, value);
  }
  return (total - lowest - highest) / (salary.length - 2);
}

const average = solve;
class Solution {
  average(salary) { return solve(salary); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, average };

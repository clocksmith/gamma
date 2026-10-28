'use strict';

// 90. Subsets II (Medium).
// Specification: https://leetcode.com/problems/subsets-ii/description/
function solve(nums) {
  const sorted = nums.slice().sort((a, b) => a - b);
  const result = [];
  function backtrack(start, current) {
    result.push(current.slice());
    for (let i = start; i < sorted.length; i++) {
      if (i > start && sorted[i] === sorted[i - 1]) continue;
      current.push(sorted[i]); backtrack(i + 1, current); current.pop();
    }
  }
  backtrack(0, []);
  return result;
}
const subsetsWithDup = solve;
class Solution { subsetsWithDup(nums) { return solve(nums); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, subsetsWithDup };

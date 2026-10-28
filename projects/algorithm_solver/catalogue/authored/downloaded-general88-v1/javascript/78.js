'use strict';

// 78. Subsets (Medium).
// Specification: https://leetcode.com/problems/subsets/description/
function solve(nums) {
  const result = [];
  function backtrack(start, current) {
    result.push(current.slice());
    for (let i = start; i < nums.length; i++) { current.push(nums[i]); backtrack(i + 1, current); current.pop(); }
  }
  backtrack(0, []);
  return result;
}
const subsets = solve;
class Solution { subsets(nums) { return solve(nums); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, subsets };

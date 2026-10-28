'use strict';

// 1770. Maximum Score from Performing Multiplication Operations (Medium).
// Specification: https://leetcode.com/problems/maximum-score-from-performing-multiplication-operations/description/
function solve(nums, multipliers) {
  const n = nums.length; const m = multipliers.length;
  const memo = new Map();
  function best(operation, left) {
    if (operation === m) return 0;
    const key = operation + ',' + left;
    if (memo.has(key)) return memo.get(key);
    const right = n - 1 - (operation - left);
    const takeLeft = nums[left] * multipliers[operation] + best(operation + 1, left + 1);
    const takeRight = nums[right] * multipliers[operation] + best(operation + 1, left);
    const result = Math.max(takeLeft, takeRight);
    memo.set(key, result);
    return result;
  }
  return best(0, 0);
}
const maximumScore = solve;
class Solution { maximumScore(nums, multipliers) { return solve(nums, multipliers); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, maximumScore };

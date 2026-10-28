'use strict';

// 396. Rotate Function (Medium).
// Specification: https://leetcode.com/problems/rotate-function/description/
function solve(nums) {
  const n = nums.length;
  let total = 0; let current = 0;
  for (let i = 0; i < n; i++) { total += nums[i]; current += i * nums[i]; }
  let best = current;
  for (let i = 1; i < n; i++) { current = current + total - n * nums[n - i]; best = Math.max(best, current); }
  return best;
}
const maxRotateFunction = solve;
class Solution { maxRotateFunction(nums) { return solve(nums); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxRotateFunction };

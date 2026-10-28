'use strict';

// 2012. Sum of Beauty in the Array (Medium).
// Specification: https://leetcode.com/problems/sum-of-beauty-in-the-array/description/
function solve(nums) {
  const n = nums.length;
  const prefMax = new Array(n); const suffMin = new Array(n);
  let cur = -Infinity;
  for (let i = 0; i < n; i++) { prefMax[i] = cur; if (nums[i] > cur) cur = nums[i]; }
  cur = Infinity;
  for (let i = n - 1; i >= 0; i--) { suffMin[i] = cur; if (nums[i] < cur) cur = nums[i]; }
  let total = 0;
  for (let i = 1; i + 1 < n; i++) {
    if (prefMax[i] < nums[i] && nums[i] < suffMin[i]) total += 2;
    else if (nums[i - 1] < nums[i] && nums[i] < nums[i + 1]) total += 1;
  }
  return total;
}
const sumOfBeauties = solve;
class Solution { sumOfBeauties(nums) { return solve(nums); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, sumOfBeauties };

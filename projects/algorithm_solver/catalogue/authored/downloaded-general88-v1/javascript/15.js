'use strict';

// 15. 3Sum (Medium).
// Specification: https://leetcode.com/problems/3sum/description/
function solve(nums) {
  const sorted = nums.slice().sort((a, b) => a - b);
  const result = [];
  for (let i = 0; i < sorted.length - 2; i++) {
    if (i > 0 && sorted[i] === sorted[i - 1]) continue;
    let left = i + 1; let right = sorted.length - 1;
    while (left < right) {
      const total = sorted[i] + sorted[left] + sorted[right];
      if (total === 0) { result.push([sorted[i], sorted[left], sorted[right]]); while (left < right && sorted[left] === sorted[left + 1]) left++; while (left < right && sorted[right] === sorted[right - 1]) right--; left++; right--; }
      else if (total < 0) left++;
      else right--;
    }
  }
  return result;
}
const threeSum = solve;
class Solution { threeSum(nums) { return solve(nums); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, threeSum };
